"""
Compile User Message Defintions first:

$ python -m pylsb.compile -i ../testing/mjvr_types.h ../testing/climber_config.h > ./examples/rnel_msg_defs.py
"""

import sys
import time

sys.path.append("../")

import pylsb
from rnel_msg_defs import *


def publisher(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(timecode=timecode)
    mod.connect(server_name=server)

    for msg_type, msg_cls in pylsb.msg_defs.items():
        if msg_type < 1000:
            continue

        print(msg_cls.type_name)
        mod.send_message(msg_cls())
        time.sleep(0.100)

    mod.send_signal(pylsb.MT_EXIT)
    print("Goodbye")


def subscriber(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(timecode=timecode)
    mod.connect(server_name=server)

    # Select the messages to receive
    mod.subscribe([msg_type for msg_type in pylsb.msg_defs.keys() if msg_type > 1000])
    mod.subscribe([pylsb.MT_EXIT])

    print("Waiting for packets...")
    while True:
        try:
            msg = mod.read_message(timeout=0.200)

            if msg is not None:
                # msg.hexdump()
                print(msg)
                if msg.name == "EXIT":
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
