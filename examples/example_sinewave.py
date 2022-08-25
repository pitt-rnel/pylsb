import sys, ctypes, time, math

sys.path.append("../")

import pylsb

# Choose a unique message type id number
MT_SINE_TEST_MSG = 9000

# Create a user defined message from a ctypes.Structure or basic ctypes
class SINE_TEST_MSG(pylsb.MessageData):
    _fields_ = [
        ("time", ctypes.c_double),
        ("value", ctypes.c_double)
    ]

    type_id: int = MT_SINE_TEST_MSG
    type_name: str = "SINE_TEST_MSG"

    def __str__(self):
        return self.pretty_print()


# Add the message definition to the pylsb module
pylsb.AddMessage(MT_SINE_TEST_MSG, msg_cls=SINE_TEST_MSG)


def publisher(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(timecode=timecode)
    mod.connect(server_name=server)

    # Build a packet to send
    msg = SINE_TEST_MSG()
    # sine params
    A = 1 # sine amplitude
    f = 2 # sine frequency
    phase = 0 # sine phase
    w = 2*math.pi*f # omega = 2*pi*f

    
    t0 = time.time() # init timer
    while True:
        try:
            # calculate and send sine value
            msg.time = time.time() - t0
            msg.value = A*math.sin(w*msg.time + phase)
            mod.send_message(msg)
            time.sleep(0.02)
        except KeyboardInterrupt:
            mod.send_signal(pylsb.MT_EXIT)
            print("Goodbye")
            break


def subscriber(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(timecode=timecode)
    mod.connect(server_name=server)

    # Select the messages to receive
    mod.subscribe([MT_SINE_TEST_MSG, pylsb.MT_EXIT])

    print("Waiting for packets...")
    while True:
        try:
            msg = mod.read_message(timeout=0.200)

            if msg is not None:
                if msg.name == "SINE_TEST_MSG":
                    print(msg.data)
                elif msg.name == "EXIT":
                    print("Goodbye.")
                    break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", default="127.0.0.1:7111", help="LSB Message Manager ip address."
    )
    parser.add_argument(
        "-t", "--timecode", action="store_true", help="Use timecode in message header"
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
        publisher(args.server, timecode=args.timecode)
    elif args.sub:
        print("pylsb Subscriber")
        subscriber(args.server, timecode=args.timecode)
    else:
        print("Unknown input")