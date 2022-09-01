import sys, ctypes, time, math

sys.path.append("../")

import pylsb

# Choose a unique message type id number
MT_SINE_TEST_MSG = 9000
MT_SINE_STOP = 9001
MT_SINE_START = 9002

# Create a user defined message from a ctypes.Structure or basic ctypes
class SINE_TEST_MSG(pylsb.MessageData):
    _fields_ = [("time", ctypes.c_double), ("value", ctypes.c_double)]

    type_id: int = MT_SINE_TEST_MSG
    type_name: str = "SINE_TEST_MSG"

    def __str__(self):
        return self.pretty_print()

class SINE_STOP(pylsb.MessageData):
    type_id: int = MT_SINE_STOP
    type_name: str = "SINE_STOP"

class SINE_START(pylsb.MessageData):
    type_id: int = MT_SINE_START
    type_name: str = "SINE_START"


# Add the message definition to the pylsb module
pylsb.AddMessage(MT_SINE_TEST_MSG, msg_cls=SINE_TEST_MSG)
pylsb.AddMessage(MT_SINE_STOP, msg_cls=SINE_STOP)
pylsb.AddMessage(MT_SINE_START, msg_cls=SINE_START)


def publisher(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(timecode=timecode)
    mod.connect(server_name=server)

    # Select the messages to receive
    mod.subscribe([MT_SINE_STOP, MT_SINE_START, pylsb.MT_EXIT])

    # Build a packet to send
    sin_msg = SINE_TEST_MSG()
    # sine params
    A = 1  # sine amplitude
    f = 2  # sine frequency
    phase = 0  # sine phase
    w = 2 * math.pi * f  # omega = 2*pi*f

    t0 = time.time()  # init timer
    pause_t0 = time.time()
    run = True
    while True:
        try:
            # calculate and send sine value
            if run:
                t = time.time() - t0
                sin_msg.time = t
                sin_msg.value = A * math.sin(w * t + phase)
                mod.send_message(sin_msg)
            msg = mod.read_message(timeout=0.020)
            if msg is not None:
                if msg.name == "SINE_STOP":
                    if run:
                        pause_t0 = time.time()
                        run = False
                        print("Stopping")
                elif msg.name == "SINE_START":
                    if not run:
                        t0 += time.time() - pause_t0
                        run = True
                        print("Starting")
                elif msg.name == "EXIT":
                    print("Goodbye")
                    break
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
