import string
import ctypes

from dataclasses import dataclass
from collections import ChainMap
from functools import lru_cache
from typing import Type, ClassVar, Optional, Any, Dict, ChainMap

core_msg_defs: Dict[int, Type["MessageData"]] = {}
user_msg_defs: Dict[int, Type["MessageData"]] = {}

msg_defs: ChainMap[int, Type["MessageData"]] = ChainMap(core_msg_defs, user_msg_defs)

# Field type name to ctypes
ctypes_map = {
    "void": ctypes.c_void_p,
    "char": ctypes.c_char,
    "unsigned char": ctypes.c_ubyte,
    "byte": ctypes.c_char,
    "int": ctypes.c_int,
    "signed int": ctypes.c_uint,
    "unsigned int": ctypes.c_uint,
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
}


MAX_NAME_LEN = 32
MAX_MESSAGE_DATA = 9000


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
    _name: ClassVar[str] = ""

    @classmethod
    def uid(cls) -> int:
        return hash_string(cls._name)

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


def msg_def(msg_cls, *args, **kwargs):
    """Decorator to add user message definitions."""
    user_msg_defs[msg_cls.uid()] = msg_cls
    return msg_cls


def core_def(msg_cls, *args, **kwargs):
    """Decorator to add core message definitions."""
    core_msg_defs[msg_cls.uid()] = msg_cls
    return msg_cls


_valid_chars = []
_valid_chars.extend(string.digits)
_valid_chars.extend(string.ascii_letters)
_valid_chars.extend(["_"])
_char_to_value = {c: i for i, c in enumerate(_valid_chars)}


@lru_cache(maxsize=128)
def hash_string(s: str) -> int:
    h = 0

    for c in reversed(s):
        h = h * 31 + _char_to_value[c]

    return h % 0xFFFFFFFFFFFFFFFF


class MessageHeader(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_double),
        ("src_uid", ctypes.c_uint64),
        ("dest_uid", ctypes.c_uint64),
        ("msg_uid", ctypes.c_uint64),
        ("num_bytes", ctypes.c_uint16),
        ("options", ctypes.c_uint16),
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


class TimeCodeMessageHeader(MessageHeader):
    _fields_ = [
        ("utc_seconds", ctypes.c_uint),
        ("utc_fraction", ctypes.c_uint),
    ]


@dataclass
class Message:
    header: MessageHeader
    data: MessageData

    @property
    def uid(self) -> int:
        return self.data.uid()

    @property
    def name(self) -> str:
        return self.data._name

    # custom print for message data
    def pretty_print(self, add_tabs=0):
        return (
            self.header.pretty_print(add_tabs) + "\n" + self.data.pretty_print(add_tabs)
        )


# START OF LSB INTERNAL MESSAGE DEFINITIONS


@core_def
class CONNECT(MessageData):
    _fields_ = [
        ("client_name", ctypes.c_char * 32),
        ("pid", ctypes.c_int),
    ]
    _name: ClassVar[str] = "CONNECT"


@core_def
class DISCONNECT(MessageData):
    _name: ClassVar[str] = "DISCONNECT"


@core_def
class SUBSCRIBE(MessageData):
    _fields_ = [("msg_name", ctypes.c_char * 32)]
    _name: ClassVar[str] = "SUBSCRIBE"


@core_def
class UNSUBSCRIBE(MessageData):
    _fields_ = [("msg_name", ctypes.c_char * 32)]
    _name: ClassVar[str] = "UNSUBSCRIBE"


@core_def
class CONNECT_ACK(MessageData):
    _fields_ = [("client_name", ctypes.c_char * 32), ("client_uid", ctypes.c_uint64)]
    _name: ClassVar[str] = "CONNECT_ACK"


@core_def
class SUBSCRIBE_ACK(MessageData):
    _fields_ = [
        ("msg_name", ctypes.c_char * 32),
        ("msg_uid", ctypes.c_uint16),
        ("success", ctypes.c_bool),
    ]
    _name: ClassVar[str] = "SUBSCRIBE_ACK"


@core_def
class UNSUBSCRIBE_ACK(MessageData):
    _fields_ = [
        ("msg_name", ctypes.c_char * 32),
        ("msg_uid", ctypes.c_uint16),
        ("success", ctypes.c_bool),
    ]
    _name: ClassVar[str] = "UNSUBSCRIBE_ACK"


@core_def
class EXIT(MessageData):
    _name: ClassVar[str] = "EXIT"
