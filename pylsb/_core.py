import ctypes

from dataclasses import dataclass
from collections import ChainMap
from typing import Type, ClassVar, Optional, Any, Dict, ChainMap

from .constants import *

core_msg_defs: Dict[int, Type["MessageData"]] = {}
user_msg_defs: Dict[int, Type["MessageData"]] = {}

msg_defs: ChainMap[int, Type["MessageData"]] = ChainMap(core_msg_defs, user_msg_defs)

# Field type name to ctypes
ctypes_map = {
    "char": ctypes.c_char,
    "unsigned char": ctypes.c_ubyte,
    "byte": ctypes.c_char,
    "int": ctypes.c_int,
    "signed int": ctypes.c_uint,
    "unsigned int": ctypes.c_uint,
    "unsigned": ctypes.c_uint,
    "short": ctypes.c_short,
    "signed short": ctypes.c_short,
    "unsigned short": ctypes.c_ushort,
    "long": ctypes.c_long,
    "signed long": ctypes.c_long,
    "unsigned long": ctypes.c_ulong,
    "long long": ctypes.c_longlong,
    "signed long long": ctypes.c_longlong,
    "unsigned long long": ctypes.c_ulonglong,
    "float": ctypes.c_float,
    "double": ctypes.c_double,
    "MODULE_ID": ctypes.c_short,
    "HOST_ID": ctypes.c_short,
    "MSG_TYPE": ctypes.c_int,
    "MSG_COUNT": ctypes.c_int,
}


def print_ctype_array(arr):
    """expand and print ctype arrays"""
    max_len = 20
    arr_len = len(arr)
    str = "{"
    for i in range(0, min(arr_len, max_len)):
        str += f"{arr[i]}, "
    if arr_len > max_len:
        str += "...}"
    else:
        str = str[:-2] + "}"
    return str


# TODO: Make this class abstract
class MessageData(ctypes.Structure):
    type_id: ClassVar[int] = -1
    type_name: ClassVar[str] = ""

    @property
    def size(self) -> int:
        return ctypes.sizeof(self)

    @property
    def buffer(self):
        return memoryview(self)

    # custom print for message data
    def pretty_print(self, add_tabs=0):
        str = "\t" * add_tabs + f"{type(self).__name__}:"
        for field_name, field_type in self._fields_:
            val = getattr(self, field_name)
            class_name = type(val).__name__
            # expand arrays
            if hasattr(val, "__len__"):
                val = print_ctype_array(val)
            str += f"\n" + "\t" * (add_tabs + 1) + f"{field_name} = ({class_name}){val}"
        return str

    def hexdump(self, length=16, sep=" "):
        src = bytes(self)
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
    def size(self) -> int:
        return ctypes.sizeof(self)

    @property
    def buffer(self):
        return memoryview(self)

    # custom print for message data
    def pretty_print(self, add_tabs=0):
        str = "\t" * add_tabs + f"{type(self).__name__}:"
        for field_name, field_type in self._fields_:
            val = getattr(self, field_name)
            class_name = type(val).__name__
            # expand arrays
            if hasattr(val, "__len__"):
                val = print_ctype_array(val)
            str += f"\n" + "\t" * (add_tabs + 1) + f"{field_name} = ({class_name}){val}"
        return str

    @property
    def get_data(self) -> Type[MessageData]:
        return msg_defs[self.msg_type]


class TimeCodeMessageHeader(MessageHeader):
    _fields_ = [
        ("utc_seconds", ctypes.c_uint),
        ("utc_fraction", ctypes.c_uint),
    ]


def get_header_cls(timecode: bool = False) -> Type[MessageHeader]:
    if timecode:
        return TimeCodeMessageHeader
    else:
        return MessageHeader


@dataclass
class Message:
    header: MessageHeader
    data: MessageData

    @property
    def type_id(self) -> int:
        return self.data.type_id

    @property
    def name(self) -> str:
        return self.data.type_name

    # custom print for message data
    def pretty_print(self, add_tabs=0):
        return (
            self.header.pretty_print(add_tabs) + "\n" + self.data.pretty_print(add_tabs)
        )


# START OF LSB INTERNAL MESSAGE DEFINITIONS
class EXIT(MessageData):
    type_id: ClassVar[int] = MT_EXIT
    type_name: ClassVar[str] = "EXIT"


core_msg_defs[MT_EXIT] = EXIT


class KILL(MessageData):
    type_id: ClassVar[int] = MT_KILL
    type_name: ClassVar[str] = "KILL"


core_msg_defs[MT_KILL] = KILL


class ACKNOWLEDGE(MessageData):
    type_id: ClassVar[int] = MT_ACKNOWLEDGE
    type_name: ClassVar[str] = "ACKNOWLEDGE"


core_msg_defs[MT_ACKNOWLEDGE] = ACKNOWLEDGE


class CONNECT(MessageData):
    _fields_ = [("logger_status", ctypes.c_short), ("daemon_status", ctypes.c_short)]
    type_id: ClassVar[int] = MT_CONNECT
    type_name: ClassVar[str] = "CONNECT"


core_msg_defs[MT_CONNECT] = CONNECT


class SUBSCRIBE(MessageData):
    _fields_ = [("msg_type", MSG_TYPE)]
    type_id: ClassVar[int] = MT_SUBSCRIBE
    type_name: ClassVar[str] = "SUBSCRIBE"


core_msg_defs[MT_SUBSCRIBE] = SUBSCRIBE


class UNSUBSCRIBE(MessageData):
    _fields_ = [("msg_type", MSG_TYPE)]
    type_id: ClassVar[int] = MT_UNSUBSCRIBE
    type_name: ClassVar[str] = "UNSUBSCRIBE"


core_msg_defs[MT_UNSUBSCRIBE] = UNSUBSCRIBE


class PAUSE_SUBSCRIPTION(MessageData):
    _fields_ = [("msg_type", MSG_TYPE)]
    type_id: ClassVar[int] = MT_PAUSE_SUBSCRIPTION
    type_name: ClassVar[str] = "PAUSE_SUBSCRIPTION"


core_msg_defs[MT_PAUSE_SUBSCRIPTION] = PAUSE_SUBSCRIPTION


class RESUME_SUBSCRIPTION(MessageData):
    _fields_ = [("msg_type", MSG_TYPE)]
    type_id: ClassVar[int] = MT_RESUME_SUBSCRIPTION
    type_name: ClassVar[str] = "RESUME_SUBSCRIPTION"


core_msg_defs[MT_RESUME_SUBSCRIPTION] = RESUME_SUBSCRIPTION


class FAIL_SUBSCRIBE(MessageData):
    _fields_ = [
        ("mod_id", MODULE_ID),
        ("reserved", ctypes.c_short),
        ("msg_type", MSG_TYPE),
    ]
    type_id: ClassVar[int] = MT_FAIL_SUBSCRIBE
    type_name: ClassVar[str] = "FAIL_SUBSCRIBE"


core_msg_defs[MT_FAIL_SUBSCRIBE] = FAIL_SUBSCRIBE


class FAILED_MESSAGE(MessageData):
    _fields_ = [
        ("dest_mod_id", MODULE_ID),
        ("reserved", ctypes.c_short * 3),
        ("time_of_failure", ctypes.c_double),
        ("msg_header", MessageHeader),
    ]
    type_id: ClassVar[int] = MT_FAILED_MESSAGE
    type_name: ClassVar[str] = "FAILED_MESSAGE"


core_msg_defs[MT_FAILED_MESSAGE] = FAILED_MESSAGE


class FORCE_DISCONNECT(MessageData):
    _fields_ = [("mod_id", ctypes.c_int)]
    type_id: ClassVar[int] = MT_FORCE_DISCONNECT
    type_name: ClassVar[str] = "FORCE_DISCONNECT"


core_msg_defs[MT_FORCE_DISCONNECT] = FORCE_DISCONNECT


class MODULE_READY(MessageData):
    _fields_ = [("pid", ctypes.c_int)]
    type_id: ClassVar[int] = MT_MODULE_READY
    type_name: ClassVar[str] = "MODULE_READY"


core_msg_defs[MT_MODULE_READY] = MODULE_READY


class SAVE_MESSAGE_LOG(MessageData):
    _fields_ = [
        ("pathname", ctypes.c_char * MAX_LOGGER_FILENAME_LENGTH),
        ("pathname_length", ctypes.c_int),
    ]
    type_id: ClassVar[int] = MT_SAVE_MESSAGE_LOG
    type_name: ClassVar[str] = "SAVE_MESSAGE_LOG"


core_msg_defs[MT_SAVE_MESSAGE_LOG] = SAVE_MESSAGE_LOG


class TIMING_MESSAGE(MessageData):
    _fields_ = [
        ("timing", ctypes.c_ushort * MAX_MESSAGE_TYPES),
        ("ModulePID", ctypes.c_int * MAX_MODULES),
        ("send_time", ctypes.c_double),
    ]
    type_id: ClassVar[int] = MT_TIMING_MESSAGE
    type_name: ClassVar[str] = "TIMING_MESSAGE"


core_msg_defs[MT_TIMING_MESSAGE] = TIMING_MESSAGE


def AddMessage(msg_type_id: int, msg_cls: Type[MessageData]):
    """Add a user message definition to the LSB module"""
    msg_defs.maps[1][msg_type_id] = msg_cls

