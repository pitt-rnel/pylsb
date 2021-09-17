from collections import defaultdict
import socket
import select
import argparse
from dataclasses import dataclass
import logging
import time
import random
import ctypes
from typing import Dict, List, Tuple, Set

import pyrtma.types
import pyrtma.constants
from pyrtma.types import Message, MessageHeader


@dataclass
class Module:

    conn: socket.socket
    address: Tuple[str, int]
    id: int = 0
    pid: int = 0
    connected: bool = False
    is_logger: bool = False

    def send_message(self, msg: Message):
        msg_size = Message.header_size + msg.header.num_data_bytes
        payload = memoryview(msg).cast("b")[:msg_size]
        self.conn.sendall(payload)

    def send_ack(self):
        # Just send a header
        header = MessageHeader()
        header.msg_type = pyrtma.types.MT["Acknowledge"]
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
    def __init__(self, ip_address: str, port: int, debug=False):

        self.ip_address = ip_address
        self.port = port
        self.timeout = 0.200
        self._debug = debug
        self.logger = logging.getLogger(f"MessageManager@{ip_address}:{port}")

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
            id=0,
            connected=True,
            is_logger=False,
        )

        self.modules[self.listen_socket] = mm_module

        self.header_size = ctypes.sizeof(MessageHeader)
        self.recv_buffer = bytearray(ctypes.sizeof(Message))
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
        connect_info = pyrtma.types.Connect.from_buffer(msg.data)
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
        msg_type_id = pyrtma.types.Subscribe.from_buffer(msg.data).value
        self.subscriptions[msg_type_id].add(src_module)

    def remove_subscription(self, src_module: Module, msg: Message):
        msg_type_id = pyrtma.types.Unsubscribe.from_buffer(msg.data).value
        # Silently let modules unsubscribe from messages that they are not subscribed to.
        self.subscriptions[msg_type_id].discard(src_module)

    def resume_subscription(self, src_module: Module, msg: Message):
        self.add_subscription(src_module, msg)

    def pause_subscription(self, src_module: Module, msg: Message):
        self.remove_subscription(src_module, msg)

    def read_message(self, sock: socket.socket) -> Message:
        # Read RTMA Header Section
        nbytes = sock.recv_into(self.recv_buffer, self.header_size, socket.MSG_WAITALL)
        msg = Message.from_buffer(self.recv_buffer)

        # Read Data Section
        if msg.header.num_data_bytes > 0:
            nbytes = sock.recv_into(
                msg.data, msg.header.num_data_bytes, socket.MSG_WAITALL
            )

        return msg

    def forward_message(self, msg: Message, wlist: List[socket.socket]):
        """ Forward a message from other modules
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
            if module.id == msg.header.dest_mod_id:
                if module.conn in wlist:
                    module.send_message(msg)
                else:
                    print("x", end="")

    def process_message(
        self, src_module: Module, msg: Message, wlist: List[socket.socket]
    ):
        msg_name = pyrtma.types.MT_BY_ID.get(msg.header.msg_type)

        if msg_name == "Connect":
            self.connect_module(src_module, msg)
            self.logger.info(f"CONNECT - {src_module!s}")
        elif msg_name == "Disconnect":
            self.disconnect_module(src_module)
            self.logger.info(f"DISCONNECT - {src_module!s}")
        elif msg_name == "Subscribe":
            self.add_subscription(src_module, msg)
            self.logger.info(f"SUBSCRIBE- {src_module!s} to {msg.msg_name}")
        elif msg_name == "Unsubscribe":
            self.remove_subscription(src_module, msg)
            self.logger.info(f"UNSUBSCRIBE - {src_module!s} from {msg.msg_name}")
        elif msg_name == "PauseSubscription":
            self.logger.info(f"PAUSE_SUBSCRIPTION - {src_module!s} to {msg.msg_name}")
            self.pause_subscription(src_module, msg)
        elif msg_name == "ResumeSubscription":
            self.resume_subscription(src_module, msg)
            self.logger.info(f"RESUME_SUBSCRIPTION - {src_module!s} to {msg.msg_name}")
        else:
            self.logger.info(f"FORWARD - {msg_name} from {src_module!s}")
            self.forward_message(msg, wlist)

    def run(self):
        try:
            while True:
                rlist, wlist, xlist = select.select(
                    self.modules.keys(), self.modules.keys(), [], self.timeout
                )

                # Check for an incoming connection request
                if len(rlist) > 0:
                    try:
                        rlist.remove(self.listen_socket)
                        (conn, address) = self.listen_socket.accept()
                        self.logger.info(
                            f"New connection accpeted from {address[0]}:{address[1]}"
                        )
                        self.sockets.append(conn)
                        self.modules[conn] = Module(conn, address)
                    except ValueError:
                        pass

                    # Randomly select the order of sockets with data.
                    random.shuffle(rlist)

                    # Read the incoming messages, process, and distribute
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

    msg_mgr = MessageManager("127.0.0.1", 7111, debug=True)

    msg_mgr.run()
