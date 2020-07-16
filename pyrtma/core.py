import ctypes 
import sys

MODULE_ID = ctypes.c_short
HOST_ID = ctypes.c_short
MSG_TYPE = ctypes.c_int
MSG_COUNT = ctypes.c_int

constants = {}
constants['MAX_MODULES'] = 200
constants['DYN_MOD_ID_START'] = 100
constants['MAX_HOSTS'] = 5
constants['MAX_MESSAGE_TYPES'] = 10000
constants['MIN_STREAM_TYPE'] = 9000
constants['MAX_TIMERS'] = 100
constants['MAX_INTERNAL_TIMERS'] = 20
constants['MAX_RTMA_MSG_TYPE'] = 99
constants['MAX_RTMA_MODULE_ID'] = 9
constants['MAX_LOGGER_FILENAME_LENGTH'] = 256
constants['MAX_CONTIGUOUS_MESSAGE_DATA'] = 9000

MID_MESSAGE_MANAGER = 0
MID_COMMAND_MODULE = 1
MID_APPLICATION_MODULE = 2
MID_NETWORK_RELAY = 3
MID_STATUS_MODULE = 4
MID_QUICKLOGGER = 5
HID_LOCAL_HOST = 0
HID_ALL_HOSTS = 0x7FFF

# RTMA INTERNAL MESSAGE TYPES

ALL_MESSAGE_TYPES = 0x7FFFFFFF

MT = {}
MT['EXIT'] = 0
MT['KILL'] = 1
MT['ACKNOWLEDGE'] = 2
MT['FAIL_SUBSCRIBE'] = 6
MT['CONNECT'] = 13
MT['DISCONNECT'] = 14
MT['SUBSCRIBE'] = 15
MT['UNSUBSCRIBE'] = 16
MT['MM_ERROR'] = 83
MT['MM_INFO'] = 84
MT['PAUSE_SUBSCRIPTION'] = 85
MT['RESUME_SUBSCRIPTION'] = 86
MT['SHUTDOWN_RTMA'] = 17
MT['SHUTDOWN_APP'] = 17
MT['SAVE_MESSAGE_LOG'] = 56
MT['MESSAGE_LOG_SAVED'] = 57
MT['PAUSE_MESSAGE_LOGGING'] = 58
MT['RESUME_MESSAGE_LOGGING'] = 59
MT['RESET_MESSAGE_LOG'] = 60
MT['DUMP_MESSAGE_LOG'] = 61
MT['FORCE_DISCONNECT'] = 82
MT['MODULE_READY'] = 26
MT['SM_EXIT'] = 48
MT['LM_EXIT'] = 55
MT['MM_READY'] = 94
MT['LM_READY'] = 96

#START OF RTMA INTERNAL MESSAGE DEFINITIONS

SUBSCRIBE = MSG_TYPE
UNSUBSCRIBE = MSG_TYPE
PAUSE_SUBSCRIPTION = MSG_TYPE
RESUME_SUBSCRIPTION = MSG_TYPE
MM_ERROR = ctypes.POINTER(ctypes.c_char)
MM_INFO = ctypes.POINTER(ctypes.c_char)


class MSG_HEADER(ctypes.Structure):
    _fields_ = [
	('serial_no', ctypes.c_int),
	('sub_sample', ctypes.c_int)]


class RTMA_MSG_HEADER(ctypes.Structure):
    _fields_ = [ 
        ('msg_type', ctypes.c_int),
        ('msg_count', ctypes.c_int),
        ('send_time', ctypes.c_double),
        ('recv_time', ctypes.c_double),
        ('src_host_id', HOST_ID),
        ('src_mod_id', MODULE_ID),
        ('dest_host_id', HOST_ID),
        ('dest_mod_id', MODULE_ID),
        ('num_data_bytes', ctypes.c_int),
        ('remaining_bytes', ctypes.c_int),
        ('is_dynamic', ctypes.c_int),
        ('reserved', ctypes.c_int)
    ]

constants['HEADER_SIZE'] = ctypes.sizeof(RTMA_MSG_HEADER)


class RTMA_MESSAGE(ctypes.Structure):
    _fields_ = [
        ('msg_type', ctypes.c_int),
        ('msg_count', MSG_COUNT),
        ('send_time', ctypes.c_double),
        ('recv_time', ctypes.c_double),
        ('src_host_id', HOST_ID),
        ('src_mod_id', MODULE_ID),
        ('dest_host_id', HOST_ID),
        ('dest_mod_id', MODULE_ID),
        ('num_data_bytes', ctypes.c_int),
        ('remaining_bytes', ctypes.c_int),
        ('is_dynamic', ctypes.c_int),
        ('reserved', ctypes.c_int),
        ('data', ctypes.c_char * constants['MAX_CONTIGUOUS_MESSAGE_DATA'])
    ]


class CONNECT(ctypes.Structure):
    _fields_ = [
        ('logger_status', ctypes.c_short), 
        ('daemon_status', ctypes.c_short)]


class FAIL_SUBSCRIBE(ctypes.Structure):
    _fields_ = [
        ('mod_id', MODULE_ID),
        ('reserved', ctypes.c_short),
        ('msg_type', MSG_TYPE)]


class FAILED_MESSAGE(ctypes.Structure):
    _fields_ = [
	('dest_mod_id', MODULE_ID),
	('reserved', ctypes.c_short * 3),
	('time_of_failure', ctypes.c_double),
	('msg_header', RTMA_MSG_HEADER)]


class FORCE_DISCONNECT(ctypes.Structure):
    _fields_ = [('mod_id', ctypes.c_int)]


class MODULE_READY(ctypes.Structure):
    _fields_ = [('pid', ctypes.c_int)]


class SAVE_MESSAGE_LOG(ctypes.Structure):
    _fields_ = [('pathname', ctypes.c_char * constants['MAX_LOGGER_FILENAME_LENGTH']),
            ('pathname_length', ctypes.c_int)]

# END OF RTMA INTERNAL MESSAGE DEFINTIONS

# Dictionary to lookup message name by message type id number
# This needs come after all the message defintions are defined
MT_BY_ID = {}
for key, value in MT.items():
    MT_BY_ID[value] = key

del key
del value

module = sys.modules['pyrtma.core']

def AddMessage(msg_name, msg_type, msg_def=None, signal=False):
    '''Add a user message definition to the rtma module'''
    mt = getattr(module, 'MT')
    mt[msg_name] = msg_type
    mt_by_id = getattr(module, 'MT_BY_ID')
    mt_by_id[msg_type] = msg_name

    if not signal:
        setattr(module, msg_name, msg_def)
    else:
        setattr(module, msg_name, MSG_TYPE)


def AddSignal(msg_name, msg_type):
    AddMessage(msg_name, msg_type, msg_def=None, signal=True)

