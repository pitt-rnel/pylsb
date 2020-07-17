import socket
import select
import time
import os

import pyrtma.core as rtma
from pyrtma.message import Message

DEBUG = False
def debug_print(msg):
    if DEBUG:
        print(msg)
    else:
        pass

class rtmaClient(object):

    def __init__(self, module_id=0, host_id=0):
       self.module_id = module_id
       self.host_id = host_id
       self.msg_count = 0
       self.self_msg_count = 0
       self.start_time = time.perf_counter()
       self.server = None
       self.connected = False

    def __del__(self):
        if self.connected:
            self.disconnect()

    def connect(self, 
                    server_name='localhost:7111',
                    logger_status=False,
                    daemon_status=False):

        self.server = server_name.split(':')
        self.server[1] = int(self.server[1])
        self.server = tuple(self.server)

        self.type = 'Socket'

        if self.type == 'NamedPipe':
            raise NotImplementedError
        elif self.type == 'Socket':
            # Create the tcp socket
            self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

            # Connect to the message server
            self.sock.connect(self.server)
            self.start_time = time.perf_counter()

            # Disable Nagle Algorithm
            self.sock.setsockopt(
                    socket.getprotobyname('tcp'),
                    socket.TCP_NODELAY,
                    1)
            
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            msg = Message(msg_name='CONNECT')
            msg.data.logger_status = int(logger_status)
            msg.data.daemon_status = int(daemon_status)

            self.send_message(msg)
            ack_msg = self.wait_for_acknowledgement()
            if ack_msg == None:
                raise Exception("Failed to receive Acknowlegement from MessageManager")

            # save own module ID from ACK if asked to be assigned dynamic ID
            if self.module_id == 0:
                self.module_id = ack_msg.rtma_header.dest_mod_id

            self.connected = True

    def disconnect(self):
        self.send_signal('DISCONNECT')
        self.sock.close()
        self.connected = False

    def send_module_ready(self):
        msg = Message(msg_name='MODULE_READY')
        msg.data.pid = os.getpid()
        self.send_message(msg)

    def _subscription_control(self, msg_list, ctrl_msg):
        if not isinstance(msg_list, list): 
            msg_list = [msg_list]

        for msg_name in msg_list:
            msg = Message(ctrl_msg)
            msg.data.value = rtma.MT[msg_name]
            self.send_message(msg)
            self.wait_for_acknowledgement()

    def subscribe(self, msg_list):
        self._subscription_control(msg_list, 'SUBSCRIBE')

    def unsubscribe(self, msg_list):
        self._subscription_control(msg_list, 'UNSUBSCRIBE')

    def pause_subscription(self):
        self._subscription_control(msg_list, 'PAUSE_SUBSCRIPTION')

    def resume_subscription(self):
        self._subscription_control(msg_list, 'RESUME_SUBSCRIPTION')

    def send_signal(self, signal_name, dest_mod_id=0, dest_host_id=0):
        signal = Message(msg_name=signal_name, signal=True)
        self.send_message(signal, dest_mod_id, dest_host_id)

    def send_message(self, msg, dest_mod_id=0, dest_host_id=0, timeout=-1):
        # Verify that the module & host ids are valid
        if dest_mod_id < 0 or dest_mod_id > rtma.constants['MAX_MODULES']:
            raise Exception(f"rtmaClient::send_message: Got invalid dest_mod_id [{dest_mod_id}]")

        if dest_host_id < 0 or dest_host_id > rtma.constants['MAX_HOSTS']:
            raise Exception(f"rtmaClient::send_message: Got invalid dest_host_id [{dest_host_id}]")

        # Assume that msg_type, num_data_bytes, data - have been filled in
        msg.rtma_header.msg_count   = self.msg_count
        msg.rtma_header.send_time   = time.perf_counter()
        msg.rtma_header.recv_time   = 0.0;
        msg.rtma_header.src_host_id = self.host_id
        msg.rtma_header.src_mod_id  = self.module_id;
        msg.rtma_header.dest_host_id = dest_host_id;
        msg.rtma_header.dest_mod_id = dest_mod_id;	

        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([], [self.sock], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select([], [self.sock], []) # blocking
        
        if writefds:
            if msg.rtma_header.num_data_bytes > 0:
                self.sock.sendall(bytes(msg.rtma_header) + bytes(msg.data))
            else:
                self.sock.sendall(msg.rtma_header)

           # debug_print(f"Sent {msg.msg_name}")
            self.msg_count+= 1
        else:
            # Socket was not ready to receive data. Drop the packet.
            print('x', end='')

    def read_message(self, timeout=-1, ack=False):
        if timeout >= 0:
            readfds, writefds, exceptfds = select.select([self.sock],[], [], timeout)
        else:
            readfds, writefds, exceptfds = select.select([self.sock],[], []) # blocking

        # Read RTMA Header Section
        if readfds:
            msg = Message()
            msg.rtma_header = rtma.RTMA_MSG_HEADER() 

            view = memoryview(msg.rtma_header).cast('b')
            nbytes = self.sock.recv_into(view, rtma.constants['HEADER_SIZE'], socket.MSG_WAITALL)
            msg.rtma_header.recv_time = time.perf_counter()
            msg.msg_name = rtma.MT_BY_ID[msg.rtma_header.msg_type]
            msg.msg_size = rtma.constants['HEADER_SIZE'] + msg.rtma_header.num_data_bytes
        else:
            return None

        # Read Data Section
        if msg.rtma_header.num_data_bytes > 0:
            msg.data = getattr(rtma, msg.msg_name)()
            view = memoryview(msg.data).cast('b')
            nbytes = self.sock.recv_into(view, msg.rtma_header.num_data_bytes, socket.MSG_WAITALL)

        return msg
		
    def wait_for_acknowledgement(self, timeout=3):
        ret = 0;
        debug_print("Waiting for ACK... ")

        # Wait Forever
        if timeout == -1: 
            while True:
                msg = self.read_message(ack=True) 
                if msg is not None:
                    if msg.rtma_header.msg_type == rtma.MT['ACKNOWLEDGE']:
                        break
                        debug_print( "Got ACK!");
            return msg
        else:
           # Wait up to timeout seconds
            time_remaining = timeout
            start_time = time.perf_counter()
            while time_remaining > 0:
                msg = self.read_message(timeout=time_remaining, ack=True);
                if msg is not None:
                    if msg.rtma_header.msg_type == rtma.MT['ACKNOWLEDGE']:
                        debug_print( "Got ACK!")
                        return msg 

                time_now = time.perf_counter()
                time_waited = time_now - start_time;
                time_remaining = timeout - time_waited;

            debug_print( "ACK timed out!");
            return None
