import sys
import ctypes
from pynats import NATSClient

# Create a user defined message from a ctypes.Structure or basic ctypes
class USER_MESSAGE(ctypes.Structure):
    _fields_ = [
            ('str', ctypes.c_byte * 16),
            ('val', ctypes.c_double),
            ('arr', ctypes.c_int * 8)
            ]

def publisher(server='nats://127.0.0.1:4222'):
    # Setup Client
    client = NATSClient(url=server)
    client.connect()

    # Build a packet to send
    msg = USER_MESSAGE()
    py_string = b'Hello World'
    msg.str[:len(py_string)] = py_string
    msg.val = 123.456
    msg.arr[:] = list(range(8))

    while True:
        c = input('Hit enter to publish a message. (Q)uit.')
        
        if c not in ['Q', 'q']:
            client.publish('TEST', payload=bytes(msg))
            print('Sent a packet')
        else:
            client.publish('EXIT')
            print('Goodbye')
            break


def subscriber(server='nats://127.0.0.1:4222'):
    # Setup Client
    client = NATSClient(url=server)
    client.connect()

    reply_msg = []
    def callback(message):
        reply_msg.append(message)

    client.subscribe('TEST', callback=callback)
    client.subscribe('EXIT', callback=callback)

    print('Waiting for packets...')
    while True:
        client.wait(count=1)
        msg = reply_msg.pop()
        if msg.subject == 'TEST':
            print(msg)
        elif msg.subject == 'EXIT':
            print('Goodbye.')
            break


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='nats://127.0.0.1:4222', help='Nats-server ip address.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pub', default=False, action='store_true', help='Run as publisher.')
    group.add_argument('--sub', default=False, action='store_true', help='Run as subscriber.')

    args = parser.parse_args()

    if args.pub:
        print('pynats Publisher')
        publisher(args.server)
    elif args.sub:
        print('pynats Subscriber')
        subscriber(args.server)
    else:
        print('Unknown input')
