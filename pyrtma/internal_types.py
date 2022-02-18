import ctypes
import sys
import io
from typing import ClassVar, Type, Optional, Any
from .constants import *

module = sys.modules["pyrtma.internal_types"]

# RTMA INTERNAL MESSAGE TYPES

MT = {}
MT["Exit"] = 0
MT["Kill"] = 1
MT["Acknowledge"] = 2
MT["FailSubscribe"] = 6
MT["FailedMessage"] = 8
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
MT["TimingMessage"] = 80

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

    @property
    def size(self):
        return ctypes.sizeof(self)

    @property
    def buffer(self):
        return memoryview(self)


class TimeCodeMessageHeader(MessageHeader):
    _fields_ = [
        ("utc_seconds", ctypes.c_uint),
        ("utc_fraction", ctypes.c_uint),
    ]


class Message:
    _header: MessageHeader
    _buffer: bytes
    _data: Any
    _data_set: bool = False

    def __init__(self, header: MessageHeader, data: Any = None):
        self.header = header

        # TODO: Add some checks for header mismatch
        if data:
            self.data = data

    def _reset(self, header: MessageHeader):
        # Allocate a buffer for the header and expected data
        self._buffer = bytearray(header.size + header.num_data_bytes)

        # Create views into the buffer
        self._view = memoryview(self._buffer)
        self._hdr_view = self._view[: header.size]
        self._data_view = self._view[header.size :]

        # Copy the header into the internal buffer
        self._hdr_view[:] = bytes(header)
        self._header = type(header).from_buffer(self._hdr_view)

        # Flag to indicate if data was unpacked
        self._data_set: bool = False

    def pack(self, format=None) -> bytes:
        # TODO: Should support other packing formats
        return self._buffer

    def unpack(self, format=None) -> Any:
        # TODO: Should support other unpacking formats
        msg_name = MT_BY_ID[self._header.msg_type]
        data = getattr(module, msg_name).from_buffer(self._data_view)
        self._data = data
        self._data_set = True
        return data

    @property
    def hdr_buffer(self):
        return self._hdr_view

    @property
    def data_buffer(self):
        return self._data_view

    @property
    def data(self):
        if not self._data_set:
            return self.unpack()
        else:
            return self._data

    @data.setter
    def data(self, new_data):
        """Copy new message data directly."""
        self._data_view[:] = bytes(new_data)
        self.unpack()

    @property
    def header_cls(self):
        return type(self._header)

    @property
    def header_size(self):
        return self._header.size

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self._header.num_data_bytes

    @header.setter
    def header(self, new_header: MessageHeader):
        self._reset(new_header)

    def dump(self):
        """Return a copy of the internal buffer."""
        return bytes(self._buffer)

    def hexdump(self, length=16, sep=" "):
        src = self._buffer
        FILTER = "".join(
            [(len(repr(chr(x))) == 3) and chr(x) or sep for x in range(256)]
        )
        for c in range(0, len(src), length):
            chars = src[c : c + length]
            hex_ = " ".join(["{:02x}".format(x) for x in chars])
            if len(hex_) > 24:
                hex_ = "{} {}".format(hex_[:24], hex_[24:])
            printable = "".join(
                ["{}".format((x <= 127 and FILTER[x]) or sep) for x in chars]
            )
            print(
                "{0:08x}  {1:{2}s} |{3:{4}s}|".format(
                    c, hex_, length * 3, printable, length
                )
            )

    @staticmethod
    def get_header_cls(timecode=False) -> Type[MessageHeader]:
        if timecode:
            return TimeCodeMessageHeader
        else:
            return MessageHeader


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


class TimingMessage(ctypes.Structure):
    _fields_ = [
        ("timing", ctypes.c_ushort * MAX_MESSAGE_TYPES),
        ("ModulePID", ctypes.c_int * MAX_MODULES),
        ("send_time", ctypes.c_double),
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
