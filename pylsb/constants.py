import ctypes

MAX_MODULES = 200
DYN_MOD_ID_START = 100
MAX_HOSTS = 5
MAX_MESSAGE_TYPES = 10000
MIN_STREAM_TYPE = 9000
MAX_TIMERS = 100
MAX_INTERNAL_TIMERS = 20
MAX_LSB_MSG_TYPE = 99
MAX_LSB_MODULE_ID = 9
MAX_LOGGER_FILENAME_LENGTH = 256
MAX_CONTIGUOUS_MESSAGE_DATA = 9000
MID_MESSAGE_MANAGER = 0
MID_COMMAND_MODULE = 1
MID_APPLICATION_MODULE = 2
MID_NETWORK_RELAY = 3
MID_STATUS_MODULE = 4
MID_QUICKLOGGER = 5
HID_LOCAL_HOST = 0
HID_ALL_HOSTS = 0x7FFF
ALL_MESSAGE_TYPES = 0x7FFFFFFF


# Internal Module IDs
MID_MESSAGE_MANAGER = 0
MID_COMMAND_MODULE = 1
MID_APPLICATION_MODULE = 2
MID_NETWORK_RELAY = 3
MID_STATUS_MODULE = 4
MID_QUICKLOGGER = 5
HID_LOCAL_HOST = 0
HID_ALL_HOSTS = 0x7FFF

# Internal Message IDs
ALL_MESSAGE_TYPES = 0x7FFFFFFF

MT_EXIT = 0
MT_KILL = 1
MT_ACKNOWLEDGE = 2
MT_FAIL_SUBSCRIBE = 6
MT_FAILED_MESSAGE = 8
MT_CONNECT = 13
MT_DISCONNECT = 14
MT_SUBSCRIBE = 15
MT_UNSUBSCRIBE = 16
MT_PAUSE_SUBSCRIPTION = 85
MT_RESUME_SUBSCRIPTION = 86
MT_SAVE_MESSAGE_LOG = 56
MT_MESSAGE_LOG_SAVED = 57
MT_PAUSE_MESSAGE_LOGGING = 58
MT_RESUME_MESSAGE_LOGGING = 59
MT_RESET_MESSAGE_LOG = 60
MT_DUMP_MESSAGE_LOG = 61
MT_FORCE_DISCONNECT = 82
MT_MODULE_READY = 26
MT_TIMING_MESSAGE = 80

# Internal typedefs
MODULE_ID = ctypes.c_short
HOST_ID = ctypes.c_short
MSG_TYPE = ctypes.c_int
MSG_COUNT = ctypes.c_int
