from collections import defaultdict
import socket
import select
import argparse
from dataclasses import dataclass
import logging
import time
import random
import ctypes
from typing import Dict, List, Tuple, Set, Type, Union

import pyrtma.internal_types
import pyrtma.constants
from pyrtma.internal_types import Message, DefaultMessage


@dataclass
class Module:

    conn: socket.socket
    address: Tuple[str, int]
    msg_cls: Type[Message]
    id: int = 0
    pid: int = 0
    connected: bool = False
    is_logger: bool = False

    def send_message(self, msg: Message):
        msg_size = self.msg_cls.header_size + msg.header.num_data_bytes
        payload = memoryview(msg).cast("b")[:msg_size]
        self.conn.sendall(payload)

    def send_ack(self):
        # Just send a header
        header = self.msg_cls.header_type()
        header.msg_type = pyrtma.internal_types.MT["Acknowledge"]
        header.send_time = time.time()
        header.src_mod_id = pyrtma.constants.MID_MESSAGE_MANAGER
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
    def __init__(
        self,
        ip_address: Union[str, int] = socket.INADDR_ANY,
        port: int = 7111,
        msg_cls: Type[Message] = DefaultMessage,
        debug=False,
    ):

        self.ip_address = ip_address
        self.port = port
        self.msg_cls = msg_cls
        self.read_timeout = 0.200
        self.write_timeout = 0  # c++ message manager uses timeout = 0 for all modules except logger modules, which uses -1 (blocking)
        self._debug = debug
        self.logger = logging.getLogger(f"MessageManager@{ip_address}:{port}")

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

        self.subscriptions: Dict[int, Set[Module]] = defaultdict(set)
        self.sockets = [self.listen_socket]
        self.start_time = time.time()

        # Disable Nagle Algorithm
        self.listen_socket.setsockopt(
            socket.getprotobyname("tcp"), socket.TCP_NODELAY, 1
        )

        # Add message manager to its module list
        mm_module = Module(
            conn=self.listen_socket,
            address=(ip_address, port),
            msg_cls=self.msg_cls,
            id=0,
            connected=True,
            is_logger=False,
        )

        self.modules[self.listen_socket] = mm_module

        self.header_size = self.msg_cls.header_size
        self.recv_buffer = bytearray(ctypes.sizeof(self.msg_cls))
        self.data_view = memoryview(self.recv_buffer[self.header_size :])

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
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

    def assign_module_id(self):
        current_ids = [mod.id for mod in self.modules.values()]
        next_id = max(current_ids) + 1

        if next_id > 100:
            return next_id
        else:
            return 10

    def connect_module(self, src_module: Module, msg: Message):
        if src_module.id == 0:
            src_module.id = self.assign_module_id()

        # Convert the data blob into the correct msg struct
        connect_info = pyrtma.internal_types.Connect.from_buffer(msg.data)
        src_module.is_logger = connect_info.logger_status == 1
        src_module.connected = True
        if src_module.is_logger:
            self.logger_modules.add(src_module)
        src_module.send_ack()

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
        src_module.send_ack()
        self.remove_module(src_module)

    def add_subscription(self, src_module: Module, msg: Message):
        sub = pyrtma.internal_types.Subscribe.from_buffer(msg.data)
        self.subscriptions[sub.msg_type].add(src_module)
        self.logger.info(f"SUBSCRIBE- {src_module!s} to MID:{sub.msg_type}")
        src_module.send_ack()

    def remove_subscription(self, src_module: Module, msg: Message):
        sub = pyrtma.internal_types.Unsubscribe.from_buffer(msg.data)
        # Silently let modules unsubscribe from messages that they are not subscribed to.
        self.subscriptions[sub.msg_type].discard(src_module)
        self.logger.info(f"UNSUBSCRIBE- {src_module!s} to MID:{sub.msg_type}")
        src_module.send_ack()

    def resume_subscription(self, src_module: Module, msg: Message):
        self.add_subscription(src_module, msg)

    def pause_subscription(self, src_module: Module, msg: Message):
        self.remove_subscription(src_module, msg)

    def read_message(self, sock: socket.socket) -> Message:
        # Read RTMA Header Section
        nbytes = sock.recv_into(self.recv_buffer, self.header_size, socket.MSG_WAITALL)
        msg = self.msg_cls.from_buffer(self.recv_buffer)

        # Read Data Section
        if msg.header.num_data_bytes > 0:
            nbytes = sock.recv_into(
                msg.data, msg.header.num_data_bytes, socket.MSG_WAITALL
            )

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
        if dest_mod_id < 0 or dest_mod_id > pyrtma.constants.MAX_MODULES:
            self.logger.error(
                f"MessageManager::forward_message: Got invalid dest_mod_id [{dest_mod_id}]"
            )

        if dest_host_id < 0 or dest_host_id > pyrtma.constants.MAX_HOSTS:
            self.logger.error(
                f"MessageManager::forward_message: Got invalid dest_host_id [{dest_host_id}]"
            )

        # Always forward to logger modules
        for module in self.logger_modules:
            if module.conn not in wlist:
                # Block until logger is ready
                select.select([], [module.conn], [], None)
            module.send_message(msg)

        # Subscriber set for this message type
        subscribers = self.subscriptions[msg.header.msg_type]

        # Send to a specific destination if it is subscribed
        if dest_mod_id > 0:
            for module in subscribers:
                if module.id == dest_mod_id:
                    if module.conn in wlist:
                        module.send_message(msg)
                        return
                    else:
                        print("x", end="")
                        return

        # Send to all subscribed modules
        for module in subscribers:
            if module.conn in wlist:
                module.send_message(msg)
            else:
                print("x", end="")

    def process_message(
        self, src_module: Module, msg: Message, wlist: List[socket.socket]
    ):
        msg_name = pyrtma.internal_types.MT_BY_ID.get(msg.header.msg_type)

        if msg_name == "Connect":
            self.connect_module(src_module, msg)
            self.logger.info(f"CONNECT - {src_module!s}")
        elif msg_name == "Disconnect":
            self.disconnect_module(src_module)
            self.logger.info(f"DISCONNECT - {src_module!s}")
        elif msg_name == "Subscribe":
            self.add_subscription(src_module, msg)
        elif msg_name == "Unsubscribe":
            self.remove_subscription(src_module, msg)
        elif msg_name == "PauseSubscription":
            self.pause_subscription(src_module, msg)
        elif msg_name == "ResumeSubscription":
            self.resume_subscription(src_module, msg)
        else:
            self.logger.info(f"FORWARD - {msg_name} from {src_module!s}")
            self.forward_message(msg, wlist)

    def run(self):
        try:
            while True:
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
                        self.modules[conn] = Module(conn, address, self.msg_cls)
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
                        msg = self.read_message(client_socket)
                        src = self.modules[client_socket]
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
    args = parser.parse_args()

    if args.addr:  # a non-empty host address was passed in.
        ip_addr = args.addr
    else:
        ip_addr = socket.INADDR_ANY

    msg_cls = Message.get_cls(args.timecode)

    msg_mgr = MessageManager(
        ip_address=ip_addr, port=args.port, msg_cls=msg_cls, debug=args.debug
    )

    msg_mgr.run()
