import sys
import time

sys.path.append("../")

from pyrtma import *

# Order of included files is important
include_files = [
    "../testing/mjvr_types.h",
    "../testing/climber_config.h",
]

# Parse the C header files with message definitions.
parse_files(include_files)


def publisher(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = Client(timecode=timecode)
    mod.connect(server_name=server)

    for name, msg in RTMA.msg_defs.items():
        mt = RTMA.MT.get(name)
        if not mt or mt < 1000:
            continue
        print(name)
        mod.send_message(msg())
        time.sleep(0.100)

    mod.send_signal("Exit")
    print("Goodbye")


def subscriber(server="127.0.0.1:7111", timecode=False):
    # Setup Client
    mod = Client(timecode=timecode)
    mod.connect(server_name=server)

    # Select the messages to receive
    mts = RTMA.MT.values()
    for mt in mts:
        if mt > 1000:
            mod.subscribe([RTMA.MT_BY_ID[mt]])
    mod.subscribe(["Exit"])

    print("Waiting for packets...")
    while True:
        try:
            msg = mod.read_message(timeout=0.200)

            if msg is not None:
                # msg.hexdump()
                print(msg)
                if msg.msg_name == "Exit":
                    print("Goodbye.")
                    break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", default="127.0.0.1:7111", help="RTMA Message Manager ip address."
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
        print("pyrtma Publisher")
        publisher(args.server, timecode=args.timecode)
    elif args.sub:
        print("pyrtma Subscriber")
        subscriber(args.server, timecode=args.timecode)
    else:
        print("Unknown input")
