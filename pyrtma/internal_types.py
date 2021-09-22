import ctypes
import sys
from typing import ClassVar, Type
from .constants import *

module = sys.modules["pyrtma.internal_types"]

# RTMA INTERNAL MESSAGE TYPES

MT = {}
MT["Exit"] = 0
MT["Kill"] = 1
MT["Acknowledge"] = 2
MT["FailSubscribe"] = 6
MT["Connect"] = 13
MT["Disconnect"] = 14
MT["Subscribe"] = 15
MT["Unsubscribe"] = 16
MT["PauseSubscription"] = 85
MT["ResumeSubscription"] = 86
MT["SaveMessageLog"] = 56
MT["MessageLogSaved"] = 57
MT["PauseMessageLogging"] = 58
MT["ResumeMessageLogging"] = 59
MT["ResetMessageLog"] = 60
MT["DumpMessageLog"] = 61
MT["ForceDisconnect"] = 82
MT["ModuleReady"] = 26

# START OF RTMA INTERNAL MESSAGE DEFINITIONS

MODULE_ID = ctypes.c_short
HOST_ID = ctypes.c_short
MSG_TYPE = ctypes.c_int
MSG_COUNT = ctypes.c_int


class MessageHeader(ctypes.Structure):
    _fields_ = [
        ("msg_type", ctypes.c_int),
        ("msg_count", ctypes.c_int),
        ("send_time", ctypes.c_double),
        ("recv_time", ctypes.c_double),
        ("src_host_id", HOST_ID),
        ("src_mod_id", MODULE_ID),
        ("dest_host_id", HOST_ID),
        ("dest_mod_id", MODULE_ID),
        ("num_data_bytes", ctypes.c_int),
        ("remaining_bytes", ctypes.c_int),
        ("is_dynamic", ctypes.c_int),
        ("reserved", ctypes.c_int),
    ]


class TimeCodeMessageHeader(MessageHeader):
    _fields_ = [
        ("utc_seconds", ctypes.c_uint),
        ("utc_fraction", ctypes.c_uint),
    ]


class Message(ctypes.Structure):
    """Subclasses of Message must implement _fields_, header_size, and header_type"""

    @staticmethod
    def get_type(timecode: bool) -> Type["Message"]:
        if timecode:
            return TimeCodeMessage
        else:
            return DefaultMessage

    def cast_data(self):
        # Get the message data type
        msg_name = MT_BY_ID[self.header.msg_type]
        return getattr(module, msg_name).from_buffer(self.data)


class DefaultMessage(Message):
    _fields_ = [
        ("header", MessageHeader),
        ("data", ctypes.c_byte * MAX_CONTIGUOUS_MESSAGE_DATA),
    ]

    header_size: ClassVar[int] = ctypes.sizeof(MessageHeader)

    header_type: ClassVar[Type[Message]] = MessageHeader


class TimeCodeMessage(Message):
    _fields_ = [
        ("header", TimeCodeMessageHeader),
        ("data", ctypes.c_byte * MAX_CONTIGUOUS_MESSAGE_DATA),
    ]

    header_size: ClassVar[int] = ctypes.sizeof(TimeCodeMessageHeader)

    header_type: ClassVar[Type[Message]] = TimeCodeMessageHeader


class Connect(ctypes.Structure):
    _fields_ = [("logger_status", ctypes.c_short), ("daemon_status", ctypes.c_short)]


class Subscribe(ctypes.Structure):
    _fields_ = [("msg_type", MSG_TYPE)]


class Unsubscribe(ctypes.Structure):
    _fields_ = [("msg_type", MSG_TYPE)]


class PauseSubscription(ctypes.Structure):
    _fields_ = [("msg_type", MSG_TYPE)]


class ResumeSubscription(ctypes.Structure):
    _fields_ = [("msg_type", MSG_TYPE)]


class FailSubscribe(ctypes.Structure):
    _fields_ = [
        ("mod_id", MODULE_ID),
        ("reserved", ctypes.c_short),
        ("msg_type", MSG_TYPE),
    ]


class FailedMessage(ctypes.Structure):
    _fields_ = [
        ("dest_mod_id", MODULE_ID),
        ("reserved", ctypes.c_short * 3),
        ("time_of_failure", ctypes.c_double),
        ("msg_header", MessageHeader),
    ]


class ForceDisconnect(ctypes.Structure):
    _fields_ = [("mod_id", ctypes.c_int)]


class ModuleReady(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_int)]


class SaveMessageLog(ctypes.Structure):
    _fields_ = [
        ("pathname", ctypes.c_char * MAX_LOGGER_FILENAME_LENGTH),
        ("pathname_length", ctypes.c_int),
    ]


# END OF RTMA INTERNAL MESSAGE DEFINTIONS

# Dictionary to lookup message name by message type id number
# This needs come after all the message defintions are defined
MT_BY_ID = {v: k for k, v in MT.items()}


def AddMessage(msg_name, msg_type, msg_def=None, signal=False):
    """Add a user message definition to the rtma module"""
    mt = getattr(module, "MT")
    mt[msg_name] = msg_type
    mt_by_id = getattr(module, "MT_BY_ID")
    mt_by_id[msg_type] = msg_name

    if not signal:
        setattr(module, msg_name, msg_def)
    else:
        setattr(module, msg_name, MSG_TYPE)


def AddSignal(msg_name, msg_type):
    AddMessage(msg_name, msg_type, msg_def=None, signal=True)
