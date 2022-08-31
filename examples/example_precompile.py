"""
Compile User Message Defintions first:

$ python -m pylsb.compile -i ../testing/mjvr_types.h ../testing/climber_config.h > ./examples/rnel_msg_defs.py

After compiling, import your definitions:
from rnel_msg_defs import *
"""

import sys
import time

sys.path.append("../")

import pylsb
from rnel_msg_defs import *


def publisher(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(name="pub_test", timecode=timecode)
    mod.connect(server_name=server)

    for msg_uid, msg_cls in user_msg_defs.items():
        print(msg_cls._name)
        mod.send_message(msg_cls())
        time.sleep(0.100)

    mod.send_message(pylsb.EXIT())
    print("Goodbye")


def subscriber(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = pylsb.Client(name="sub_test", timecode=timecode)
    mod.connect(server_name=server)

    # Select the messages to receive
    mod.subscribe(list(user_msg_defs.values()))
    mod.subscribe([pylsb.EXIT])

    print("Waiting for packets...")
    while True:
        try:
            msg = mod.read_message(timeout=0.200)

            if msg is not None:
                if msg.name == "ACKNOWLEDGE":
                    pass
                elif msg.name == "EXIT":
                    print("Goodbye.")
                    break
                else:
                    print(msg.name)

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
