import sys
import ctypes
import time
import multiprocessing

sys.path.append('../')
from pynats import NATSClient

def publisher_loop(pub_id=0, num_msgs=100000, msg_size=128, num_subscribers=0, server='nats://127.0.0.1:4222'):
    # Setup Client
    client = NATSClient(url=server)
    client.connect()

    reply_msg = []
    def callback(message):
        reply_msg.append(message)

    client.subscribe('SUBSCRIBER_READY', callback=callback) 

    # Signal that publisher is ready
    client.publish('PUBLISHER_READY')

    # Wait for the subscribers to be ready
    num_subscribers_ready = 0
    while num_subscribers_ready < num_subscribers:
        client.wait(count=1)
        re_msg = reply_msg.pop()
        if re_msg.subject == 'SUBSCRIBER_READY':
            num_subscribers_ready += 1

    # Create TEST message with dummy data
    msg = create_test_msg(msg_size)()
    if msg_size > 0:
        msg.data[:] = list(range(msg_size))

    # Send loop
    tic = time.perf_counter()
    for n in range(num_msgs):
        client.publish('TEST', payload=bytes(msg))
    toc = time.perf_counter()

    client.publish('PUBLISHER_DONE')
    
    additional_bytes = b'PUB  00\r\n\r\n'
    total_msg_size = len(additional_bytes) + ctypes.sizeof(msg)

    # Stats
    dur = toc - tic
    data_rate =  total_msg_size * num_msgs / float(1048576) / dur
    print(f"Publisher[{pub_id}] -> {num_msgs} messages | {int(num_msgs/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")


def subscriber_loop(sub_id=0, num_msgs=100000, msg_size=128, server='nats://127.0.0.1:4222'):
    # Setup Client
    client = NATSClient(url=server)
    client.connect()

    reply_msg = []
    def callback(message):
        reply_msg.append(message)

    client.subscribe('TEST', callback=callback)
    client.subscribe('EXIT', callback=callback)
    client.publish('SUBSCRIBER_READY')

    # Read Loop (Start clock after first TEST msg received)
    msg_count = 0
    while msg_count < num_msgs:
        client.wait(count=1)
        msg = reply_msg.pop()

        if msg.subject == 'TEST':
            if msg_count == 0:
                test_msg_size = len(msg.subject.encode()) + len(msg.reply.encode()) + len(msg.payload)
                tic = time.perf_counter()
            toc = time.perf_counter()
            msg_count += 1
        elif msg.subject == 'EXIT':
            break
            
    client.publish('SUBSCRIBER_DONE')

    # Stats
    additional_bytes = b'MSG 0 00\r\n\r\n'
    total_msg_size = len(additional_bytes) + test_msg_size

    dur = toc - tic
    data_rate = (total_msg_size * num_msgs) / float(1048576) / dur
    if msg_count == num_msgs:
        print(f"Subscriber [{sub_id:d}] -> {msg_count} messages | {int((msg_count-1)/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")
    else:
        print(f"Subscriber [{sub_id:d}] -> {msg_count} ({int(msg_count/num_msgs *100):0d}%) messages | {int((msg_count-1)/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")



def create_test_msg(msg_size):
    class TEST(ctypes.Structure):
        _fields_ = [('data', ctypes.c_byte * msg_size)]
    return TEST


if __name__ == '__main__':
    import argparse

    # Configuration flags for bench utility
    parser = argparse.ArgumentParser(description='pynats bench test utility')
    parser.add_argument('-ms', default=128, type=int, dest='msg_size', help='Messge size in bytes.')
    parser.add_argument('-n', default=100000, type=int, dest='num_msgs', help='Number of messages.')
    parser.add_argument('-np', default=1, type=int, dest='num_publishers', help='Number of concurrent publishers.')
    parser.add_argument('-ns', default=1, type=int, dest='num_subscribers', help='Number of concurrent subscribers.')
    parser.add_argument('-s',default='nats://127.0.0.1:4222', dest='server', help='RTMA message manager ip address (default: 127.0.0.1:7111)')
    args = parser.parse_args()

    #Main Thread nats client
    client = NATSClient(url=args.server)
    client.connect()

    reply_msg = []
    def callback(message):
        reply_msg.append(message)

    client.subscribe('PUBLISHER_READY', callback=callback)
    client.subscribe('PUBLISHER_DONE', callback=callback)
    client.subscribe('SUBSCRIBER_READY', callback=callback)
    client.subscribe('SUBSCRIBER_DONE', callback=callback)

    print("Initializing publisher processses...")
    publishers = []
    for n in range(args.num_publishers):
        publishers.append(
                multiprocessing.Process(
                    target=publisher_loop,
                    kwargs={
                        'pub_id': n+1,
                        'num_msgs': int(args.num_msgs/args.num_publishers),
                        'msg_size': args.msg_size, 
                        'num_subscribers': args.num_subscribers,
                        'server': args.server})
                    )
        publishers[n].start()

    # Wait for publisher processes to be established
    publishers_ready = 0
    while publishers_ready < args.num_publishers:
        client.wait(count=1)
        msg = reply_msg.pop()
        if msg.subject == 'PUBLISHER_READY':
            publishers_ready += 1

    print('Waiting for subscriber processes...')
    subscribers = []
    for n in range(args.num_subscribers):
        subscribers.append(
                multiprocessing.Process(
                    target=subscriber_loop,
                    kwargs={
                        'sub_id': n+1,
                        'num_msgs': args.num_msgs,
                        'msg_size': args.msg_size, 
                        'server': args.server})
                    )
        subscribers[n].start()

    print("Starting Test...")
    print(f"Packet size: {args.msg_size}")
    print(f'Sending {args.num_msgs} messages...')

    # Wait for subscribers to finish
    abort_timeout = max(args.num_msgs/1000, 10) #seconds
    abort_start = time.perf_counter()

    subscribers_done = 0
    publishers_done = 0
    while (subscribers_done < args.num_subscribers) and (publishers_done < args.num_publishers):
        client.wait(count=1)
        msg = reply_msg.pop()
        if msg.subject == 'SUBSCRIBER_DONE':
            subscriber_done += 1
        elif msg.subject == 'PUBLISHER_DONE':
            publishers_done += 1

        if (time.perf_counter() - abort_start) > abort_timeout: 
            time.sleep(1)
            client.publish('EXIT')
            print('Test Timeout! Sending Exit Signal...')
            break

    for publisher in publishers:
        publisher.join()

    for subscriber in subscribers:
        subscriber.join()
    
    print('Done!')
