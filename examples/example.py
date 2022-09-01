import sys
import ctypes

sys.path.append("../")

import pylsb

# Create a user defined message from a ctypes.Structure or basic ctypes
@pylsb.msg_def
class USER_MESSAGE(pylsb.MessageData):
    _fields_ = [
        ("str", ctypes.c_byte * 64),
        ("val", ctypes.c_double),
        ("arr", ctypes.c_int * 8),
    ]

    _name: str = "USER_MESSAGE"


def publisher(server="127.0.0.1:7111"):
    # Setup Client
    mod = pylsb.Client(name="test_pub")
    mod.connect(server_name=server)

    # Build a packet to send
    msg = USER_MESSAGE()
    py_string = b"Hello World"
    msg.str[: len(py_string)] = py_string
    msg.val = 123.456
    msg.arr[:] = list(range(8))

    while True:
        c = input("Hit enter to publish a message. (Q)uit.")

        if c not in ["Q", "q"]:
            mod.send_message(msg)
            print("Sent a packet")
        else:
            mod.send_message(pylsb.EXIT())
            print("Goodbye")
            break


def subscriber(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(name="sub_test")
    mod.connect(server_name=server)

    # Select the messages to receive
    mod.subscribe([USER_MESSAGE, pylsb.EXIT])

    print("Waiting for packets...")
    while True:
        try:
            msg = mod.read_message(timeout=0.200)

            if msg is not None:
                if msg.name == "USER_MESSAGE":
                    msg.data.hexdump()
                    print("")
                    print(msg.pretty_print())
                elif msg.uid == pylsb.EXIT.uid():
                    print("Goodbye.")
                    break
        except KeyboardInterrupt:
            break

    mod.unsubscribe(["USER_MESSAGE", "EXIT"])
    msg = mod.read_message(timeout=0.200)
    msg = mod.read_message(timeout=0.200)
    mod.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", default="127.0.0.1:7111", help="LSB Message Manager ip address."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--pub", default=False, action="store_true", help="Run as publisher."
    )
    group.add_argument(
        "--sub", default=False, action="store_true", help="Run as subscriber."
    )

    args = parser.parse_args()

    if args.pub:
        print("pylsb Publisher")
        publisher(args.server)
    elif args.sub:
        print("pylsb Subscriber")
        subscriber(args.server)
    else:
        print("Unknown input")
