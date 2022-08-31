import socket
import select
import time
import os
import ctypes

from ._core import *
from .constants import *

from functools import wraps
from typing import List, Optional, Tuple, Type, Union, Dict

__all__ = [
    "ClientError",
    "MessageManagerNotFound",
    "NotConnectedError",
    "ConnectionLost",
    "AcknowledgementTimeout",
    "InvalidDestinationModule",
    "InvalidDestinationHost",
    "Client",
]


class ClientError(Exception):
    """Base exception for all Client Errors."""

    pass


class MessageManagerNotFound(ClientError):
    """Raised when unable to connect to message manager."""

    pass


class NotConnectedError(ClientError):
    """Raised when the client tries to read/write while not connected."""

    pass


class ConnectionLost(ClientError):
    """Raised when there is a connection error with the server."""

    pass


class AcknowledgementTimeout(ClientError):
    """Raised when client does not receive ack from message manager."""

    pass


class InvalidDestinationModule(ClientError):
    """Raised when client tries to send to an invalid module."""

    pass


class InvalidDestinationHost(ClientError):
    """Raised when client tries to send to an invalid host."""

    pass


def requires_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.connected:
            raise NotConnectedError
        else:
            return func(self, *args, **kwargs)

    return wrapper


class Client(object):
    def __init__(
        self, name: str, timecode: bool = False,
    ):
        self._uid = hash_string(name)
        self.name = name
        self._msg_count = 0
        self._server = ("", -1)
        self._connected = False
        self._header_cls = get_header_cls(timecode)
        self._recv_buffer = bytearray(1024 ** 2)
        self._pid = os.getpid()
        self._subs = set()

    def __del__(self):
        if self._connected:
            try:
                self.disconnect()
            except ClientError:
                """Siliently ignore any errors at this point."""
                pass

    def connect(
        self, server_name: str = "localhost:7111",
    ):

        if self.connected:
            raise RuntimeError(
                "Can not connect while there is already an active connection."
            )
        addr, port = server_name.split(":")
        self._server = (addr, int(port))

        # Create the tcp socket
        self._sock = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )

        # Connect to the message server
        try:
            self._connected = True
            self._sock.connect(self._server)
        except ConnectionRefusedError as e:
            self._connected = False
            raise MessageManagerNotFound(
                f"No message manager server responding at {self.ip_addr}:{self.port}"
            ) from e

        # Disable Nagle Algorithm
        self._sock.setsockopt(socket.getprotobyname("tcp"), socket.TCP_NODELAY, 1)

        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        msg = CONNECT()
        msg.client_name = self.name.encode()
        msg.pid = self._pid
        self.send_message(msg)

        # Wait for connection ack
        self.read_message(3)

        if not self.connected:
            self._sock.close()
            raise RuntimeError("Failed to connect to MM Server.")

    def disconnect(self):
        try:
            if self._connected:
                self.send_message(DISCONNECT())
        finally:
            self._sock.close()
            self._connected = False

    @property
    def server(self) -> Tuple[str, int]:
        return self._server

    @property
    def ip_addr(self) -> str:
        return self._server[0]

    @property
    def port(self) -> int:
        return self._server[1]

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def msg_count(self) -> int:
        return self._msg_count

    @property
    def uid(self) -> int:
        return self._uid

    @property
    def header_cls(self) -> Type[MessageHeader]:
        return self._header_cls

    @property
    def subscriptions(self) -> Tuple[str]:
        return tuple(self._subs)

    @requires_connection
    def subscribe(self, msg_list: List[Union[str, Type[MessageData]]]):
        if not isinstance(msg_list, list):
            msg_list = [msg_list]

        msg = SUBSCRIBE()
        for msg_type in msg_list:
            if type(msg_type) is str:
                name = msg_type
            elif issubclass(msg_type, MessageData):
                name = msg_type._name
            else:
                RuntimeError("Invalid args to subscribe.")
            if len(name) > 32:
                print(f"Skipping: Name exceeds 32 chars: {name}")
                continue
            msg.msg_name = name.encode()
            self.send_message(msg)

    @requires_connection
    def unsubscribe(self, msg_list: List[Union[str, Type[MessageData]]]):
        if not isinstance(msg_list, list):
            msg_list = [msg_list]

        msg = UNSUBSCRIBE()
        for msg_type in msg_list:
            if type(msg_type) is str:
                msg.msg_name = msg_type.encode()
            elif issubclass(msg_type, MessageData):
                msg.msg_name = msg_type._name.encode()
            self.send_message(msg)

    @requires_connection
    def send_message(
        self, msg_data: MessageData, dest: Optional[str] = None, timeout: float = -1,
    ):

        # Assume that msg_type, num_data_bytes, data - have been filled in
        header = self._header_cls()
        header.timestamp = time.time()
        header.src_uid = self.uid
        header.dest_uid = 0 if dest is None else hash_string(dest)
        header.msg_uid = msg_data.uid()
        header.num_bytes = ctypes.sizeof(msg_data)

        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([], [self._sock], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select(
                [], [self._sock], []
            )  # blocking

        if writefds:
            self._sendall(header)
            if header.num_bytes > 0:
                self._sendall(msg_data)

            self._msg_count += 1

        else:
            # Socket was not ready to receive data. Drop the packet.
            print("x", end="")

    def _sendall(self, buffer: bytearray):
        try:
            self._sock.sendall(buffer)
        except ConnectionError as e:
            self._connected = False
            raise ConnectionLost from e

    @requires_connection
    def read_message(self, timeout: Union[int, float] = -1) -> Optional[Message]:
        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([self._sock], [], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select(
                [self._sock], [], []
            )  # blocking

        # Read LSB Header Section
        if readfds:
            header = self._header_cls()
            try:
                nbytes = self._sock.recv_into(header, header.size, socket.MSG_WAITALL)
                """
                Note:
                MSG_WAITALL Flag:
                The receive request will complete only when one of the following events occurs:
                The buffer supplied by the caller is completely full.
                The connection has been closed.
                The request has been canceled or an error occurred.
                """

                if nbytes != header.size:
                    self._connected = False
                    raise ConnectionLost

                header.recv_time = time.time()
            except ConnectionError:
                raise ConnectionLost
        else:
            return None

        # Read Data Section
        data_cls = msg_defs.get(header.msg_uid)
        if data_cls is not None:
            data = data_cls()
        else:
            raise RuntimeError(f"Unknown message id of {header.msg_uid} received.")

        if header.num_bytes:
            try:
                nbytes = self._sock.recv_into(
                    data, header.num_bytes, socket.MSG_WAITALL
                )

                if nbytes != header.num_bytes:
                    self._connected = False
                    raise ConnectionLost
            except ConnectionError:
                raise ConnectionLost

        self._process_control_message(header, data)
        return Message(header, data)

    def _process_control_message(self, header: MessageHeader, msg_data: MessageData):
        msg_uid = header.msg_uid
        if msg_uid == CONNECT_ACK.uid():
            print(f"Client {msg_data.client_name.decode()} connected.")
        elif msg_uid == SUBSCRIBE_ACK.uid():
            print(f"Client subscribed to {msg_data.msg_name.decode()}.")
            self._subs.add(msg_data.msg_name.decode())
        elif msg_uid == UNSUBSCRIBE_ACK.uid():
            print(f"Client unsubscribed to {msg_data.msg_name.decode()}.")
            self._subs.remove(msg_data.msg_name.decode())

    def discard_messages(self, timeout: float = 1) -> bool:
        """Read and discard messages in socket buffer up to timeout.
        Returns: True if all messages available have been read.
        """
        msg = 1
        time_remaining = timeout
        start_time = time.perf_counter()
        while msg is not None and time_remaining > 0:
            msg = self.read_message(timeout=0)
            time_now = time.perf_counter()
            time_waited = time_now - start_time
            time_remaining = timeout - time_waited
        return not msg

    def __str__(self) -> str:
        # TODO: Make this better.
        return f"Client(client_uid={self.uid}, server={self.server}, connected={self.connected}."
