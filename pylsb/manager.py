import socket
import select
import argparse
import logging
import time
import random
import ctypes
import os

from ._core import *

from typing import Dict, List, Tuple, Set, Type, Union, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter


@dataclass
class _Client:

    conn: socket.socket
    address: Tuple[str, int]
    header_cls: Type[MessageHeader]
    uid: int = -1
    name: str = ""
    pid: int = 0
    connected: bool = False
    is_logger: bool = False

    def send_message(self, header: MessageHeader, payload: Union[bytes, MessageData]):
        self.conn.sendall(header)
        self.conn.sendall(payload)

    def close(self):
        self.conn.close()

    def __str__(self):
        return f"Client UID: {self.uid} @ {self.address[0]}:{self.address[1]}"

    def __hash__(self):
        return self.conn.__hash__()


class MessageManager:
    def __init__(
        self,
        ip_address: Union[str, int] = socket.INADDR_ANY,
        port: int = 7111,
        header_cls: Type[MessageHeader] = MessageHeader,
        debug=False,
    ):

        if ip_address == socket.INADDR_ANY:
            self.ip_address = ""  # bind and Module require a string input, '' is treated as INADDR_ANY by bind
        elif isinstance(ip_address, str):
            self.ip_address = ip_address
        else:
            raise TypeError("Invalid argument type for ip address.")

        self.port = port

        self.header_cls = header_cls
        self.header_size = ctypes.sizeof(self.header_cls)
        self.header_buffer = bytearray(self.header_size)
        self.header_view = memoryview(self.header_buffer)

        self.read_timeout = 0.200
        self.write_timeout = 0
        self._debug = debug

        self.logger = logging.getLogger(f"MessageManager@{ip_address}:{port}")

        self.console_log_level = (
            logging.INFO
        )  # should eventually change this to WARNING or INFO. Could also tie to _debug property

        # Create the tcp listening socket
        self.listen_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        self.listen_socket.bind((self.ip_address, self.port))
        self.listen_socket.listen(socket.SOMAXCONN)
        self.clients: Dict[socket.socket, _Client] = {}

        self.subscriptions: Dict[int, Set[_Client]] = defaultdict(set)
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
        self.mm_client = _Client(
            conn=self.listen_socket,
            address=(self.ip_address, port),
            header_cls=self.header_cls,
            uid=0,
            pid=os.getpid(),
            connected=True,
            is_logger=False,
        )

        self.clients[self.listen_socket] = self.mm_client

        self.data_buffer = bytearray(1024 ** 2)
        self.data_view = memoryview(self.data_buffer)

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

    @property
    def header(self) -> MessageHeader:
        return self.header_cls.from_buffer(self.header_view)

    def connect_client(self, client: _Client):  # returns a success code
        msg = CONNECT.from_buffer(self.data_buffer)

        client.name = msg.client_name.decode()
        client.uid = hash_string(client.name.lower())
        client.pid = msg.pid
        client.connected = True

        # Confirm the connection
        header = self.header_cls()
        header.timestamp = time.time()
        header.src_uid = self.mm_client.uid
        header.dest_uid = client.uid
        header.msg_uid = CONNECT_ACK.uid()
        header.num_bytes = ctypes.sizeof(CONNECT_ACK)

        ack_msg = CONNECT_ACK()
        ack_msg.client_name = client.name.encode()
        ack_msg.client_uid = client.uid
        client.send_message(header, ack_msg)

        return True

    def disconnect_client(self, client: _Client):
        # Drop all subscriptions for this module
        for msg_uid, subscriber_set in self.subscriptions.items():
            subscriber_set.discard(client)

        # Drop from our client mapping
        client.close()
        del self.clients[client.conn]

    def add_subscription(self, client: _Client):
        msg = SUBSCRIBE.from_buffer(self.data_buffer)
        msg_name = msg.msg_name.decode()
        msg_uid = hash_string(msg_name)

        self.subscriptions[hash_string(msg_name)].add(client)
        self.logger.info(f"SUBSCRIBE- {client!s} to {msg_name}:{msg_uid}")

        # Confirm the subscription
        header = self.header_cls()
        header.timestamp = time.time()
        header.src_uid = self.mm_client.uid
        header.dest_uid = client.uid
        header.msg_uid = SUBSCRIBE_ACK.uid()
        header.num_bytes = ctypes.sizeof(SUBSCRIBE_ACK)

        ack_msg = SUBSCRIBE_ACK()
        ack_msg.msg_name = msg_name.encode()
        ack_msg.msg_uid = msg_uid
        ack_msg.success = True
        client.send_message(header, ack_msg)

    def remove_subscription(self, client: _Client):
        msg = UNSUBSCRIBE.from_buffer(self.data_buffer)
        # Silently let modules unsubscribe from messages that they are not subscribed to.
        msg_name = msg.msg_name.decode()
        msg_uid = hash_string(msg_name)
        self.subscriptions[msg_uid].discard(client)
        self.logger.info(f"UNSUBSCRIBE- {client!s} to {msg_name}:{msg_uid}.")

        # Confirm removal of subscription
        header = self.header_cls()
        header.timestamp = time.time()
        header.src_uid = self.mm_client.uid
        header.dest_uid = client.uid
        header.msg_uid = UNSUBSCRIBE_ACK.uid()
        header.num_bytes = ctypes.sizeof(UNSUBSCRIBE_ACK)

        ack_msg = UNSUBSCRIBE_ACK()
        ack_msg.msg_name = msg_name.encode()
        ack_msg.msg_uid = msg_uid
        ack_msg.success = True
        client.send_message(header, ack_msg)

    def read_message(self, sock: socket.socket) -> bool:
        # Read LSB Header Section
        nbytes = sock.recv_into(
            self.header_buffer, self.header_size, socket.MSG_WAITALL
        )

        if nbytes != self.header_size:
            client = self.clients[sock]
            self.logger.warning(
                f"DROPPING - {client!s} - No header returned from sock.recv_into."
            )
            self.disconnect_client(client)
            return False

        # Read Data Section
        data_size = self.header.num_bytes
        if data_size:
            nbytes = sock.recv_into(self.data_buffer, data_size, socket.MSG_WAITALL)

            if nbytes != data_size:
                client = self.clients[sock]
                self.logger.warning(
                    f"DROPPING - {client!s} - No data returned from sock.recv_into."
                )
                self.disconnect_client(client)
                return False
        return True

    def forward_message(
        self,
        header: MessageHeader,
        data: Union[bytes, MessageData],
        wlist: List[socket.socket],
    ):
        # Specific Client Destination
        dest_uid = header.dest_uid

        # Subscriber set for this message type
        subscribers = self.subscriptions[header.msg_uid]

        # Send to a specific destination if it is subscribed
        if dest_uid > 0:
            for client in subscribers:
                if client.uid == dest_uid:
                    if client.conn in wlist:
                        try:
                            client.send_message(header, data)
                        except ConnectionError as err:
                            self.logger.error(
                                f"Connection Error on write to {client!s} - {err!s}"
                            )
                        return
                    else:
                        print("x", end="", flush=True)
                        return
            return  # if specified dest_mod_id is not in subscribers, do not send message (other than to loggers)

        # Send to all subscribed modules
        for client in subscribers:
            if client.conn in wlist:
                try:
                    client.send_message(header, data)
                except ConnectionError as err:
                    self.logger.error(
                        f"Connection Error on write to {client!s} - {err!s}"
                    )
                    print("x", end="", flush=True)
            else:
                print("x", end="", flush=True)

    def process_message(self, client: _Client, wlist: List[socket.socket]):
        hdr = self.header
        msg_uid = hdr.msg_uid

        if msg_uid == CONNECT.uid():
            if self.connect_client(client):
                self.logger.info(f"CONNECT - {client!s}")
        elif msg_uid == DISCONNECT.uid():
            self.disconnect_client(client)
            self.logger.info(f"DISCONNECT - {client!s}")
        elif msg_uid == SUBSCRIBE.uid():
            self.add_subscription(client)
        elif msg_uid == UNSUBSCRIBE.uid():
            self.remove_subscription(client)
        else:
            self.logger.debug(f"FORWARD - msg_type:{hdr.msg_uid} from {client!s}")
            data = self.data_view[: hdr.num_bytes]
            self.forward_message(hdr, data, wlist)

        # message counts
        self.message_counts[hdr.msg_uid] += 1

    def run(self):
        try:
            while True:
                rlist, _, _ = select.select(
                    self.clients.keys(), [], [], self.read_timeout
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
                        self.clients[conn] = _Client(conn, address, self.header_cls)
                    except ValueError:
                        pass

                    # Randomly select the order of sockets with data.
                    random.shuffle(rlist)

                    # Check whichs clients are ready to receive data
                    if rlist:
                        _, wlist, _ = select.select(
                            [], self.clients.keys(), [], self.write_timeout
                        )
                    else:
                        continue

                    for client_socket in rlist:
                        src = self.clients[client_socket]
                        try:
                            got_msg = self.read_message(client_socket)
                        except ConnectionError as err:
                            self.logger.error(
                                f"Connection Error on read, disconnecting  {src!s} - {err!s}"
                            )
                            self.disconnect_client(src)
                            continue

                        if got_msg:
                            self.process_message(src, wlist)

        except KeyboardInterrupt:
            self.logger.info("Stopping Message Manager")
        finally:
            for mod in self.clients:
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
    args = parser.parse_args()

    if args.addr:  # a non-empty host address was passed in.
        ip_addr = args.addr
    else:
        ip_addr = socket.INADDR_ANY

    msg_mgr = MessageManager(ip_address=ip_addr, port=args.port, debug=args.debug,)

    msg_mgr.run()
