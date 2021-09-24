import socket
import select
import time
import os
import ctypes
from typing import List
import pyrtma.internal_types
from pyrtma.internal_types import Message
from pyrtma.constants import *

DEBUG = False


def debug_print(msg):
    if DEBUG:
        print(msg)
    else:
        pass


class Client(object):
    def __init__(self, module_id: int = 0, host_id: int = 0, timecode: bool = False):
        self.module_id = module_id
        self.host_id = host_id
        self.msg_count = 0
        self.start_time = time.time()
        self.server = None
        self.connected = False
        self.msg_cls = Message.get_cls(timecode)

    def __del__(self):
        if self.connected:
            self.disconnect()

    def connect(
        self,
        server_name: str = "localhost:7111",
        logger_status: bool = False,
        daemon_status: bool = False,
    ):

        self.server = server_name.split(":")
        self.server[1] = int(self.server[1])
        self.server = tuple(self.server)

        self.type = "Socket"

        if self.type == "NamedPipe":
            raise NotImplementedError
        elif self.type == "Socket":
            # Create the tcp socket
            self.sock = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
            )

            # Connect to the message server
            self.sock.connect(self.server)
            self.start_time = time.time()

            # Disable Nagle Algorithm
            self.sock.setsockopt(socket.getprotobyname("tcp"), socket.TCP_NODELAY, 1)

            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            msg = pyrtma.internal_types.Connect()
            msg.logger_status = int(logger_status)
            msg.daemon_status = int(daemon_status)

            self.send_message(msg)
            ack_msg = self.wait_for_acknowledgement()
            if ack_msg is None:
                raise Exception("Failed to receive Acknowlegement from MessageManager")

            # save own module ID from ACK if asked to be assigned dynamic ID
            if self.module_id == 0:
                self.module_id = ack_msg.header.dest_mod_id

            self.connected = True

    def disconnect(self):
        self.send_signal("Disconnect")
        self.sock.close()
        self.connected = False

    def send_module_ready(self):
        msg = pyrtma.internal_types.ModuleReady()
        msg.data.pid = os.getpid()
        self.send_message(msg)

    def _subscription_control(self, msg_list: List[str], ctrl_msg: str):
        if not isinstance(msg_list, list):
            msg_list = [msg_list]

        if ctrl_msg == "Subscribe":
            msg = pyrtma.internal_types.Subscribe()
        elif ctrl_msg == "Unsubscribe":
            msg = pyrtma.internal_types.Subscribe()
        elif ctrl_msg == "PauseSubscription":
            msg = pyrtma.internal_types.PauseSubscription()
        elif ctrl_msg == "ResumeSubscription":
            msg = pyrtma.internal_types.ResumeSubscription()
        else:
            raise TypeError("Unknown control message type.")

        for msg_name in msg_list:
            msg.msg_type = pyrtma.internal_types.MT[msg_name]
            self.send_message(msg)

    def subscribe(self, msg_list: List[str]):
        self._subscription_control(msg_list, "Subscribe")

    def unsubscribe(self, msg_list: List[str]):
        self._subscription_control(msg_list, "Unsubscribe")

    def pause_subscription(self, msg_list: List[str]):
        self._subscription_control(msg_list, "PauseSubscription")

    def resume_subscription(self, msg_list: List[str]):
        self._subscription_control(msg_list, "ResumeSubscription")

    def send_signal(
        self,
        signal_name: str,
        dest_mod_id: int = 0,
        dest_host_id: int = 0,
        timeout: float = -1,
    ):

        # Verify that the module & host ids are valid
        if dest_mod_id < 0 or dest_mod_id > MAX_MODULES:
            raise Exception(
                f"rtmaClient::send_message: Got invalid dest_mod_id [{dest_mod_id}]"
            )

        if dest_host_id < 0 or dest_host_id > MAX_HOSTS:
            raise Exception(
                f"rtmaClient::send_message: Got invalid dest_host_id [{dest_host_id}]"
            )

        # Assume that msg_type, num_data_bytes, data - have been filled in
        header = self.msg_cls.header_type()
        header.msg_type = pyrtma.internal_types.MT[signal_name]
        header.msg_count = self.msg_count
        header.send_time = time.time()
        header.recv_time = 0.0
        header.src_host_id = self.host_id
        header.src_mod_id = self.module_id
        header.dest_host_id = dest_host_id
        header.dest_mod_id = dest_mod_id
        header.num_data_bytes = 0

        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([], [self.sock], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select(
                [], [self.sock], []
            )  # blocking

        if writefds:
            self.sock.sendall(header)

            # debug_print(f"Sent {msg.msg_name}")
            self.msg_count += 1

        else:
            # Socket was not ready to receive data. Drop the packet.
            print("x", end="")

    def send_message(
        self,
        msg_data: ctypes.Structure,
        dest_mod_id: int = 0,
        dest_host_id: int = 0,
        timeout: float = -1,
    ):
        # Verify that the module & host ids are valid
        if dest_mod_id < 0 or dest_mod_id > MAX_MODULES:
            raise Exception(
                f"rtmaClient::send_message: Got invalid dest_mod_id [{dest_mod_id}]"
            )

        if dest_host_id < 0 or dest_host_id > MAX_HOSTS:
            raise Exception(
                f"rtmaClient::send_message: Got invalid dest_host_id [{dest_host_id}]"
            )

        # Assume that msg_type, num_data_bytes, data - have been filled in
        header = self.msg_cls.header_type()
        header.msg_type = pyrtma.internal_types.MT[msg_data.__class__.__name__]
        header.msg_count = self.msg_count
        header.send_time = time.time()
        header.recv_time = 0.0
        header.src_host_id = self.host_id
        header.src_mod_id = self.module_id
        header.dest_host_id = dest_host_id
        header.dest_mod_id = dest_mod_id
        header.num_data_bytes = ctypes.sizeof(msg_data)

        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([], [self.sock], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select(
                [], [self.sock], []
            )  # blocking

        if writefds:
            self.sock.sendall(header)
            if header.num_data_bytes > 0:
                self.sock.sendall(msg_data)

            # debug_print(f"Sent {msg.msg_name}")
            self.msg_count += 1

        else:
            # Socket was not ready to receive data. Drop the packet.
            print("x", end="")

    def read_message(self, timeout=-1, ack=False):
        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([self.sock], [], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select(
                [self.sock], [], []
            )  # blocking

        # Read RTMA Header Section
        if readfds:
            msg = self.msg_cls()
            view = memoryview(msg.header).cast("b")
            nbytes = self.sock.recv_into(view, msg.header_size, socket.MSG_WAITALL)
            assert (
                nbytes == msg.header_size
            ), "Did not send all the header to message manager."
            msg.header.recv_time = time.time()
            msg.msg_name = pyrtma.internal_types.MT_BY_ID[msg.header.msg_type]
            msg.msg_size = msg.header_size + msg.header.num_data_bytes
        else:
            return None

        # Read Data Section
        if msg.header.num_data_bytes > 0:
            nbytes = self.sock.recv_into(
                msg.data, msg.header.num_data_bytes, socket.MSG_WAITALL
            )

        return msg

    def wait_for_acknowledgement(self, timeout: float = 3):
        ret = 0
        debug_print("Waiting for ACK... ")

        # Wait Forever
        if timeout == -1:
            while True:
                msg = self.read_message(ack=True)
                if msg is not None:
                    if msg.header.msg_type == pyrtma.internal_types.MT["Acknowledge"]:
                        break
                        debug_print("Got ACK!")
            return msg
        else:
            # Wait up to timeout seconds
            time_remaining = timeout
            start_time = time.perf_counter()
            while time_remaining > 0:
                msg = self.read_message(timeout=time_remaining, ack=True)
                if msg is not None:
                    if msg.header.msg_type == pyrtma.internal_types.MT["Acknowledge"]:
                        debug_print("Got ACK!")
                        return msg

                time_now = time.perf_counter()
                time_waited = time_now - start_time
                time_remaining = timeout - time_waited

            debug_print("ACK timed out!")
            return None
