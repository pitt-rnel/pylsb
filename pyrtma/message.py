from pyrtma.core import *


def bytes2str(raw_bytes):
    """Helper to convert a ctypes bytes array of null terminated strings to a
    list"""
    return raw_bytes.decode("ascii").strip("\x00").split("\x00")


class Message(object):
    def __init__(self, msg_name=None, msg_type=None, signal=False, msg_def=None):
        self.msg_name = msg_name
        self.rtma_header = None
        self.data = None
        self.msg_size = 0

        if msg_name is not None:
            self.rtma_header = RTMA_MSG_HEADER()
            self.msg_size = constants["HEADER_SIZE"]

            if msg_type is None:
                self.rtma_header.msg_type = MT[msg_name]
            else:
                self.rtma_header.msg_type = msg_type

            if not signal:
                if msg_def is None:
                    self.data = getattr(module, msg_name)()
                else:
                    self.data = msg_def()

                self.msg_size += ctypes.sizeof(self.data)
                self.rtma_header.num_data_bytes = ctypes.sizeof(self.data)

    def __repr__(self):
        if self.rtma_header is None:
            return "Empty Message"

        s = f"Type:\t{self.msg_name}\n"
        s += "---Header---\n"
        for name, ctype in self.rtma_header._fields_:
            s += f"{name}:\t {getattr(self.rtma_header, name)}\n"

        s += "\n"
        s += "---Data---\n"
        if self.data is not None:
            if hasattr(self.data, "_fields_"):
                for name, ctype in self.data._fields_:
                    try:
                        # Try to convert bytes to a string list
                        if getattr(self.data, name)._type_ == ctypes.c_byte:
                            s += f"{name}:\t {bytes2str(bytes(getattr(self.data, name)))}\n"
                        else:
                            if hasattr(getattr(self.data, name), "_length_"):
                                s += f"{name}:\t {getattr(self.data, name)[:]}\n"
                            else:
                                s += f"{name}:\t {getattr(self.data, name)}\n"
                    except AttributeError:
                        s += f"{name}:\t {getattr(self.data, name)}\n"
            else:
                s += f"{name}:\t {self.data}\n"

        return s

    def __str__(self):
        return self.__repr__()
