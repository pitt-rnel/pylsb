import socket
import select
import argparse
import logging
import time
import random
import ctypes
import os

import pylsb.internal_types
from pylsb.internal_types import Message, MessageHeader, LSB

from typing import Dict, List, Tuple, Set, Type, Union, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter


@dataclass
class Module:

    conn: socket.socket
    address: Tuple[str, int]
    header_cls: Type[MessageHeader]
    id: int = 0
    pid: int = 0
    connected: bool = False
    is_logger: bool = False

    def send_message(self, msg: Message):
        self.conn.sendall(msg.pack())

    def send_ack(self):
        # Just send a header
        header = self.header_cls()
        header.msg_type = LSB.MT["Acknowledge"]
        header.send_time = time.time()
        header.src_mod_id = LSB.constants.MID_MESSAGE_MANAGER
        header.dest_mod_id = self.id
        header.num_data_bytes = 0

        self.conn.sendall(header)

    def close(self):
        self.conn.close()

    def __str__(self):
        return f"Module ID: {self.id} @ {self.address[0]}:{self.address[1]}"

    def __hash__(self):
        return self.conn.__hash__()


class MessageManager:

    _keep_running = True

    def __init__(
        self,
        ip_address: Union[str, int] = socket.INADDR_ANY,
        port: int = 7111,
        timecode=False,
        debug=False,
        send_msg_timing=True,
    ):

        self.ip_address = ip_address
        self.port = port

        self.header_cls = Message.set_header_cls(timecode)

        self.read_timeout = 0.200
        self.write_timeout = 0  # c++ message manager uses timeout = 0 for all modules except logger modules, which uses -1 (blocking)
        self._debug = debug
        self.b_send_msg_timing = send_msg_timing
        self.logger = logging.getLogger(f"MessageManager@{ip_address}:{port}")
        self.console_log_level = (
            logging.INFO
        )  # should eventually change this to WARNING or INFO. Could also tie to _debug property

        if ip_address == socket.INADDR_ANY:
            ip_address = ""  # bind and Module require a string input, '' is treated as INADDR_ANY by bind

        # Create the tcp listening socket
        self.listen_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        self.listen_socket.bind((ip_address, port))
        self.listen_socket.listen(socket.SOMAXCONN)
        self.modules: Dict[socket.socket, Module] = {}
        self.logger_modules: Set[Module] = set()
        self.next_dynamic_mod_id_offset = 0

        self.subscriptions: Dict[int, Set[Module]] = defaultdict(set)
        self.sockets = [self.listen_socket]
        self.start_time = time.time()

        # dictionary of message type ids and message counts, reset each time timing_message is sent
        self.message_counts = Counter()
        self.t_last_message_count = time.time()
        self.min_timing_message_period = 0.9

        # Disable Nagle Algorithm
        self.listen_socket.setsockopt(
            socket.getprotobyname("tcp"), socket.TCP_NODELAY, 1
        )

        # Add message manager to its module list
        mm_module = Module(
            conn=self.listen_socket,
            address=(ip_address, port),
            header_cls=self.header_cls,
            id=0,
            pid=os.getpid(),
            connected=True,
            is_logger=False,
        )

        self.modules[self.listen_socket] = mm_module

        self._buffer = bytearray(1024**2)

        # Address Reuse allowed for testing
        if debug:
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._configure_logging()
        self.logger.info("Message Manager Initialized.")

    def _configure_logging(self) -> None:
        # Logging Configuration
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
        )

        # Console Log
        console = logging.StreamHandler()
        console.setLevel(self.console_log_level)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

    def assign_module_id(self):
        current_ids = [mod.id for mod in self.modules.values()]

        MAX_DYN_IDS = LSB.constants.MAX_MODULES - LSB.constants.DYN_MOD_ID_START
        for i in range(0, MAX_DYN_IDS):

            mod_id = self.next_dynamic_mod_id_offset + LSB.constants.DYN_MOD_ID_START
            self.next_dynamic_mod_id_offset += 1
            if self.next_dynamic_mod_id_offset == MAX_DYN_IDS:
                self.next_dynamic_mod_id_offset = 0

            # check if mod id is already used, if it is, continue looping until we find an unused one
            if mod_id not in current_ids:
                return mod_id

        # if we exit loop without returning, we failed to find a valid id
        self.logger.error(
            f"MessageManager::assign_module_id: All valid dynamic IDs are in use"
        )

    def connect_module(
        self, src_module: Module, msg: Message
    ):  # returns a success code
        src_mod_id = msg.header.src_mod_id
        if src_mod_id == 0:
            src_module.id = self.assign_module_id()
        else:
            current_ids = [mod.id for mod in self.modules.values()]
            if src_mod_id in current_ids:  # cannot have multiple modules with same ID
                self.logger.info(f"CONNECT - {src_module!s}")
                self.logger.error(
                    f"MessageManager::connect_module: Module ID {src_module!s} already in use, connection refused."
                )
                self.remove_module(src_module)
                return False
            src_module.id = src_mod_id

        # Convert the data blob into the correct msg struct
        src_module.is_logger = msg.data.logger_status == 1
        src_module.connected = True
        if src_module.is_logger:
            self.logger_modules.add(src_module)
        return True

    def remove_module(self, module: Module):
        # Drop all subscriptions for this module
        for msg_type, subscriber_set in self.subscriptions.items():
            subscriber_set.discard(module)

        # Discard from logger module set if needed
        self.logger_modules.discard(module)

        # Drop from our module mapping
        module.close()
        del self.modules[module.conn]

    def disconnect_module(self, src_module: Module):
        # src_module.send_ack() # moved to process_message
        self.remove_module(src_module)

    def add_subscription(self, src_module: Module, msg: Message):
        sub = pylsb.internal_types.Subscribe.from_buffer(msg.data)
        self.subscriptions[sub.msg_type].add(src_module)
        self.logger.info(f"SUBSCRIBE- {src_module!s} to MT:{sub.msg_type}")

    def remove_subscription(self, src_module: Module, msg: Message):
        sub = pylsb.internal_types.Unsubscribe.from_buffer(msg.data)
        # Silently let modules unsubscribe from messages that they are not subscribed to.
        self.subscriptions[sub.msg_type].discard(src_module)
        self.logger.info(f"UNSUBSCRIBE- {src_module!s} to MT:{sub.msg_type}")

    def resume_subscription(self, src_module: Module, msg: Message):
        self.add_subscription(src_module, msg)

    def pause_subscription(self, src_module: Module, msg: Message):
        self.remove_subscription(src_module, msg)

    def register_module_ready(self, src_module: Module, msg: Message):
        mr = pylsb.internal_types.ModuleReady.from_buffer(msg.data)
        src_module.pid = mr.pid

    def read_message(self, sock: socket.socket) -> Optional[Message]:
        msg = Message(buffer=self._buffer)

        # Read LSB Header Section
        nbytes = sock.recv_into(msg.hdr_buffer, msg.header_size, socket.MSG_WAITALL)

        if nbytes != msg.header_size:
            mod = self.modules[sock]
            self.logger.warning(
                f"DROPPING - {mod!s} - No header returned from sock.recv_into."
            )
            self.remove_module(mod)
            return None

        # Read Data Section
        if msg.data_size:
            nbytes = sock.recv_into(msg.data_buffer, msg.data_size, socket.MSG_WAITALL)

            if nbytes != msg.data_size:
                mod = self.modules[sock]
                self.logger.warning(
                    f"DROPPING - {mod!s} - No data returned from sock.recv_into."
                )
                self.remove_module(mod)
                return None

        return msg

    def forward_message(self, msg: Message, wlist: List[socket.socket]):
        """Forward a message from other modules
        The given message will be forwarded to:
            - all subscribed logger modules (ALWAYS)
            - if the message has a destination address, and it is subscribed to by that destination it will be forwarded only there
            - if the message has no destination address, it will be forwarded to all subscribed modules
        """

        dest_mod_id = msg.header.dest_mod_id
        dest_host_id = msg.header.dest_host_id

        # Verify that the module & host ids are valid
        if dest_mod_id < 0 or dest_mod_id > LSB.constants.MAX_MODULES:
            self.logger.error(
                f"MessageManager::forward_message: Got invalid dest_mod_id [{dest_mod_id}]"
            )

        if dest_host_id < 0 or dest_host_id > LSB.constants.MAX_HOSTS:
            self.logger.error(
                f"MessageManager::forward_message: Got invalid dest_host_id [{dest_host_id}]"
            )

        # Always forward to logger modules
        self.send_to_loggers(msg, wlist)

        # Subscriber set for this message type
        subscribers = self.subscriptions[msg.header.msg_type]

        # Send to a specific destination if it is subscribed
        if dest_mod_id > 0:
            for module in subscribers:
                if module.id == dest_mod_id:
                    if module.conn in wlist:
                        try:
                            module.send_message(msg)
                        except ConnectionError as err:
                            self.logger.error(
                                f"Connection Error on write to {module!s} - {err!s}"
                            )
                            print("x", end="", flush=True)
                            self.send_failed_message(module, msg, time.time(), wlist)
                        return
                    else:
                        print("x", end="", flush=True)
                        self.send_failed_message(module, msg, time.time(), wlist)
                        return
            return  # if specified dest_mod_id is not in subscribers, do not send message (other than to loggers)

        # Send to all subscribed modules
        for module in subscribers:
            if module.conn in wlist:
                try:
                    module.send_message(msg)
                except ConnectionError as err:
                    self.logger.error(
                        f"Connection Error on write to {module!s} - {err!s}"
                    )
                    print("x", end="", flush=True)
                    self.send_failed_message(module, msg, time.time(), wlist)
            else:
                print("x", end="", flush=True)
                self.send_failed_message(module, msg, time.time(), wlist)

    def send_to_loggers(self, msg: Message, wlist: List[socket.socket]):
        for module in self.logger_modules:
            if module.conn not in wlist:
                # Block until logger is ready
                select.select([], [module.conn], [], None)
            try:
                module.send_message(msg)
            except ConnectionError as err:
                self.logger.error(f"Connection Error on write to {module!s} - {err!s}")
                print("x", end="", flush=True)
                self.send_failed_message(
                    module, msg, time.time(), wlist
                )  # this could result in inifite recursion, this is prevented by send_failed_message returning if failed message type is failed_message.

    def send_ack(self, src_module: Module, wlist: List[socket.socket]):
        # src_module.send_ack()

        header = self.header_cls()
        header.msg_type = LSB.MT["Acknowledge"]
        header.send_time = time.time()
        header.src_mod_id = LSB.constants.MID_MESSAGE_MANAGER
        header.dest_mod_id = src_module.id
        header.num_data_bytes = 0

        ack_msg = Message(header, buffer=self._buffer)
        try:
            src_module.send_message(ack_msg)
        except ConnectionError as err:
            self.logger.error(f"Connection Error on write to {src_module!s} - {err!s}")
            print("x", end="", flush=True)
            self.send_failed_message(src_module, ack_msg, time.time(), wlist)

        # Always forward to logger modules
        self.send_to_loggers(ack_msg, wlist)

    def send_failed_message(
        self,
        dest_module: Module,
        msg: Message,
        time_of_failure: float,
        wlist: List[socket.socket],
    ):

        header = self.header_cls()
        data = pylsb.internal_types.FailedMessage()

        header.msg_type = LSB.MT["FailedMessage"]
        header.send_time = time.time()
        header.src_mod_id = LSB.constants.MID_MESSAGE_MANAGER
        header.num_data_bytes = ctypes.sizeof(data)

        data.dest_mod_id = dest_module.id
        data.time_of_failure = time_of_failure
        data.msg_header = msg.header

        failed_msg = Message(header, data, buffer=self._buffer)

        if (
            failed_msg.data.msg_header.msg_type == LSB.MT["FailedMessage"]
        ):  # avoid unlikely infinite recursion
            return

        # send to logger modules AND modules subscribed to FAILED_MESSAGE
        self.forward_message(failed_msg, wlist)

        # add to message count
        self.message_counts[failed_msg.header.msg_type] += 1

    def send_timing_message(self, wlist: List[socket.socket]):

        header = self.header_cls()
        data = pylsb.internal_types.TimingMessage()

        header.msg_type = LSB.MT["TimingMessage"]
        header.send_time = time.time()
        header.src_mod_id = LSB.constants.MID_MESSAGE_MANAGER
        header.num_data_bytes = ctypes.sizeof(data)

        tmsg = Message(header, data, buffer=self._buffer)
        tmsg.data.send_time = time.time()

        for (mt, count) in self.message_counts.items():
            tmsg.data.timing[mt] = count
        self.message_counts.clear()

        for mod in self.modules.values():
            tmsg.data.ModulePID[mod.id] = mod.pid

        self.forward_message(tmsg, wlist)

    def process_message(
        self, src_module: Module, msg: Message, wlist: List[socket.socket]
    ):
        msg_name = LSB.MT_BY_ID.get(msg.header.msg_type)

        if msg_name == "Connect":
            if self.connect_module(src_module, msg):
                self.send_ack(src_module, wlist)
                self.logger.info(f"CONNECT - {src_module!s}")
        elif msg_name == "Disconnect":
            self.send_ack(src_module, wlist)
            self.disconnect_module(src_module)
            self.logger.info(f"DISCONNECT - {src_module!s}")
        elif msg_name == "Subscribe":
            self.add_subscription(src_module, msg)
            self.send_ack(src_module, wlist)
        elif msg_name == "Unsubscribe":
            self.remove_subscription(src_module, msg)
            self.send_ack(src_module, wlist)
        elif msg_name == "PauseSubscription":
            self.pause_subscription(src_module, msg)
            self.send_ack(src_module, wlist)
        elif msg_name == "ResumeSubscription":
            self.resume_subscription(src_module, msg)
            self.send_ack(src_module, wlist)
        elif msg_name == "ModuleReady":  # used to store module pids
            self.register_module_ready(src_module, msg)
        else:
            if msg_name:
                self.logger.debug(f"FORWARD - {msg_name} from {src_module!s}")
            else:
                self.logger.debug(
                    f"FORWARD - {msg.header.msg_type} from {src_module!s}"
                )
            self.forward_message(msg, wlist)

        # message counts
        self.message_counts[msg.header.msg_type] += 1
        if (
            self.b_send_msg_timing
            and (time.time() - self.t_last_message_count)
            > self.min_timing_message_period
        ):
            self.send_timing_message(wlist)
            self.t_last_message_count = time.time()

    def close(self):
        self._keep_running = False

    def run(self):
        try:
            while self._keep_running:
                rlist, _, _ = select.select(
                    self.modules.keys(), [], [], self.read_timeout
                )

                # Check for an incoming connection request
                if len(rlist) > 0:
                    try:
                        rlist.remove(self.listen_socket)
                        (conn, address) = self.listen_socket.accept()
                        self.logger.info(
                            f"New connection accepted from {address[0]}:{address[1]}"
                        )

                        # Disable Nagle Algorithm
                        conn.setsockopt(
                            socket.getprotobyname("tcp"), socket.TCP_NODELAY, 1
                        )

                        self.sockets.append(conn)
                        self.modules[conn] = Module(conn, address, self.header_cls)
                    except ValueError:
                        pass

                    # Randomly select the order of sockets with data.
                    random.shuffle(rlist)

                    # Check whichs clients are ready to receive data
                    if rlist:
                        _, wlist, _ = select.select(
                            [], self.modules.keys(), [], self.write_timeout
                        )

                    for client_socket in rlist:
                        src = self.modules[client_socket]
                        try:
                            msg = self.read_message(client_socket)
                        except ConnectionError as err:
                            self.logger.error(
                                f"Connection Error on read, disconnecting  {src!s} - {err!s}"
                            )
                            self.disconnect_module(src)
                            continue

                        if msg:
                            self.process_message(src, msg, wlist)

        except KeyboardInterrupt:
            self.logger.info("Stopping Message Manager")
        finally:
            for mod in self.modules:
                mod.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--addr",
        type=str,
        default="",
        help="Listener address. IP address/hostname as a string. Default is '' which is evaluated as socket.INADDR_ANY.",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=7111, help="Listener port. Default is 7111."
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument(
        "-t", "--timecode", action="store_true", help="Use timecode in message header"
    )
    parser.add_argument(
        "-T",
        "--disable_timing_msg",
        action="store_true",
        help="Disable sending of TIMING_MESSAGE",
    )
    args = parser.parse_args()

    if args.addr:  # a non-empty host address was passed in.
        ip_addr = args.addr
    else:
        ip_addr = socket.INADDR_ANY

    msg_mgr = MessageManager(
        ip_address=ip_addr,
        port=args.port,
        timecode=args.timecode,
        debug=args.debug,
        send_msg_timing=(not args.disable_timing_msg),
    )

    msg_mgr.run()
