import ctypes
import sys
from typing import Type, Any, Optional, ClassVar, Dict, Union
from dataclasses import dataclass, field

module = sys.modules["pylsb.internal_types"]


class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


# LSB INTERNAL MESSAGE TYPES
@dataclass
class _LSB:
    defines: Dict[str, Any] = field(default_factory=AttributeDict)
    typedefs: Dict[str, Any] = field(default_factory=AttributeDict)
    structs: Dict[str, Any] = field(default_factory=AttributeDict)
    constants: Dict[str, Union[int, float, str]] = field(default_factory=AttributeDict)
    msg_defs: Dict[str, Any] = field(default_factory=AttributeDict)
    MID: Dict[str, int] = field(default_factory=AttributeDict)
    MT: Dict[str, int] = field(default_factory=AttributeDict)

    @property
    def MT_BY_ID(self) -> Dict[int, str]:
        return {v: k for k, v in self.MT.items()}


# Store all the context of our session here
LSB = _LSB()

LSB.MT["Exit"] = 0
LSB.MT["Kill"] = 1
LSB.MT["Acknowledge"] = 2
LSB.MT["FailSubscribe"] = 6
LSB.MT["FailedMessage"] = 8
LSB.MT["Connect"] = 13
LSB.MT["Disconnect"] = 14
LSB.MT["Subscribe"] = 15
LSB.MT["Unsubscribe"] = 16
LSB.MT["PauseSubscription"] = 85
LSB.MT["ResumeSubscription"] = 86
LSB.MT["SaveMessageLog"] = 56
LSB.MT["MessageLogSaved"] = 57
LSB.MT["PauseMessageLogging"] = 58
LSB.MT["ResumeMessageLogging"] = 59
LSB.MT["ResetMessageLog"] = 60
LSB.MT["DumpMessageLog"] = 61
LSB.MT["ForceDisconnect"] = 82
LSB.MT["ModuleReady"] = 26
LSB.MT["TimingMessage"] = 80

LSB.constants["MAX_MODULES"] = 200
LSB.constants["DYN_MOD_ID_START"] = 100
LSB.constants["MAX_HOSTS"] = 5
LSB.constants["MAX_MESSAGE_TYPES"] = 10000
LSB.constants["MIN_STREAM_TYPE"] = 9000
LSB.constants["MAX_TIMERS"] = 100
LSB.constants["MAX_INTERNAL_TIMERS"] = 20
LSB.constants["MAX_LSB_MSG_TYPE"] = 99
LSB.constants["MAX_LSB_MODULE_ID"] = 9
LSB.constants["MAX_LOGGER_FILENAME_LENGTH"] = 256
LSB.constants["MAX_CONTIGUOUS_MESSAGE_DATA"] = 9000
LSB.constants["MID_MESSAGE_MANAGER"] = 0
LSB.constants["MID_COMMAND_MODULE"] = 1
LSB.constants["MID_APPLICATION_MODULE"] = 2
LSB.constants["MID_NETWORK_RELAY"] = 3
LSB.constants["MID_STATUS_MODULE"] = 4
LSB.constants["MID_QUICKLOGGER"] = 5
LSB.constants["HID_LOCAL_HOST"] = 0
LSB.constants["HID_ALL_HOSTS"] = 0x7FFF
LSB.constants["ALL_MESSAGE_TYPES"] = 0x7FFFFFFF

# START OF LSB INTERNAL MESSAGE DEFINITIONS

MODULE_ID = ctypes.c_short
HOST_ID = ctypes.c_short
MSG_TYPE = ctypes.c_int
MSG_COUNT = ctypes.c_int

LSB.typedefs["MODULE_ID"] = "short"
LSB.typedefs["HOST_ID"] = "short"
LSB.typedefs["MSG_TYPE"] = "int"
LSB.typedefs["MSG_COUNT"] = "int"


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
    _header: Optional[MessageHeader] = None
    _buffer: bytearray
    _data: Any = None
    _data_set: bool = False
    header_cls: ClassVar[Type[MessageHeader]] = MessageHeader
    DEFAULT_DATA_SIZE: ClassVar[int] = 128

    def __init__(
        self,
        header: Optional[MessageHeader] = None,
        data: Any = None,
        buffer: Optional[bytearray] = None,
    ):
        if buffer:
            # User provided shared buffer
            self._buffer = buffer
        else:
            # Default allocation
            self._buffer = bytearray(self.header_size + Message.DEFAULT_DATA_SIZE)

        # Create view into the buffer
        self._view = memoryview(self._buffer)

        if header:
            self.header = header

        if data:
            self.data = data

    def _copy_header(self, header: MessageHeader):
        # Check header type match
        assert isinstance(header, self.header_cls)

        msg_sz = header.size + header.num_data_bytes

        # Extend the buffer for the header and expected data if needed
        if (msg_sz) > self._bufsz:
            self._view.release()
            self._buffer.extend(bytearray(msg_sz - self._bufsz))

            # Create view into the buffer
            self._view = memoryview(self._buffer)

        # Copy the header into the internal buffer
        self._hdr_view[:] = bytes(header)
        self._header = type(header).from_buffer(self._hdr_view)

        self._data_set: bool = False

    def _new_header_from_buffer(self):
        """Set new header into the message. Assumes header is filled in."""
        header = Message.header_cls.from_buffer(self._view[: self.header_size])
        msg_sz = header.size + header.num_data_bytes

        # Extend the buffer for the header and expected data if needed
        if (msg_sz) > self._bufsz:
            # Remove current header reference from view
            del header

            self._view.release()
            self._buffer.extend(bytearray((msg_sz) - self._bufsz))
            # Create view into the buffer
            self._view = memoryview(self._buffer)

            # Create header from new view
            header = Message.header_cls.from_buffer(self._view[: self.header_size])

        self._header = header

        # Flag to indicate if data was unpacked
        self._data_set: bool = False

    def pack(self, format=None) -> bytes:
        # TODO: Should support other packing formats
        return self._view[: self.size]

    def unpack(self, format=None) -> Any:
        # TODO: Should support other unpacking formats
        msg_name = LSB.MT_BY_ID[self._header.msg_type]
        data = LSB.msg_defs[msg_name].from_buffer(self._data_view)
        self._data = data
        self._data_set = True
        return data

    @property
    def _bufsz(self) -> int:
        return len(self._buffer)

    @property
    def hdr_buffer(self):
        return self._view

    @property
    def _hdr_view(self):
        return self._view[: self.header_size]

    @property
    def _data_view(self):
        return self._view[self.header_size : self.size]

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
    def header_size(self) -> int:
        return ctypes.sizeof(Message.header_cls)

    @property
    def header(self) -> MessageHeader:
        if self._header is None:
            self._new_header_from_buffer()
        return self._header

    @header.setter
    def header(self, new_header: MessageHeader):
        self._copy_header(new_header)

    @property
    def data_size(self) -> int:
        return self.header.num_data_bytes

    @property
    def size(self) -> int:
        return self.header_size + self.data_size

    def dump(self) -> bytes:
        """Return a copy of the internal buffer."""
        return bytes(self._buffer)

    def hexdump(self, length=16, sep=" "):
        src = self._buffer[: self.size]
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
    def set_header_cls(timecode=False) -> Type[MessageHeader]:
        if timecode:
            Message.header_cls = TimeCodeMessageHeader
            return TimeCodeMessageHeader
        else:
            Message.header_cls = MessageHeader
            return MessageHeader

    def __repr__(self):
        str = __msg_data_print__(self._header)
        if self._header.num_data_bytes:
            str += f"\n\tdata = {__msg_data_print__(self.data, 1)}"
        return str


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
        ("pathname", ctypes.c_char * LSB.constants.MAX_LOGGER_FILENAME_LENGTH),
        ("pathname_length", ctypes.c_int),
    ]


class TimingMessage(ctypes.Structure):
    _fields_ = [
        ("timing", ctypes.c_ushort * LSB.constants.MAX_MESSAGE_TYPES),
        ("ModulePID", ctypes.c_int * LSB.constants.MAX_MODULES),
        ("send_time", ctypes.c_double),
    ]


LSB.msg_defs.Connect = Connect
LSB.msg_defs.Unsubscribe = Unsubscribe
LSB.msg_defs.Subscribe = Subscribe
LSB.msg_defs.PauseSubscription = PauseSubscription
LSB.msg_defs.ResumeSubscription = ResumeSubscription
LSB.msg_defs.FailedMessage = FailedMessage
LSB.msg_defs.ForceDisconnect = ForceDisconnect
LSB.msg_defs.ModuleReady = ModuleReady
LSB.msg_defs.SaveMessageLog = SaveMessageLog
LSB.msg_defs.TimingMessage = TimingMessage

# END OF LSB INTERNAL MESSAGE DEFINTIONS


def AddMessage(msg_name, msg_type, msg_def=None, signal=False):
    """Add a user message definition to the LSB module"""
    LSB.MT[msg_name] = msg_type

    if not signal:
        setattr(msg_def, "__repr__", __msg_data_print__)
        setattr(LSB.msg_defs, msg_name, msg_def)
    else:
        setattr(LSB.msg_defs, msg_name, MSG_TYPE)


def AddSignal(msg_name, msg_type):
    AddMessage(msg_name, msg_type, msg_def=None, signal=True)


# custom print for message data
def __msg_data_print__(self, add_tabs=0):
    str = "\t" * add_tabs + f"{type(self).__name__}:"
    for field_name, field_type in self._fields_:
        val = getattr(self, field_name)
        class_name = type(val).__name__
        # expand arrays
        if hasattr(val, "__len__"):
            val = __c_arr_print__(val)
        str += f"\n" + "\t" * (add_tabs + 1) + f"{field_name} = ({class_name}){val}"
    return str


# expand c arrays to print
def __c_arr_print__(arr):
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
