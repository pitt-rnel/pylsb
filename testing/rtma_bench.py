import sys
import ctypes
import time
import multiprocessing

sys.path.append('../')
import pyrtma

def publisher_loop(pub_id=0, num_msgs=10000, msg_size=512, num_subscribers=1, ready_flag=None, server='127.0.0.1:7111'):
    # Register user defined message types
    pyrtma.AddMessage(msg_name='TEST', msg_type=5000, msg_def=create_test_msg(msg_size))
    pyrtma.AddMessage(msg_name='SUBSCRIBER_READY', msg_type=5001, signal=True)

    # Setup Client
    mod = pyrtma.rtmaClient()
    mod.connect(server_name=server)
    mod.send_module_ready()
    mod.subscribe('SUBSCRIBER_READY') 

    # Signal that publisher is ready
    if ready_flag is not None:
        ready_flag.set()

    # Wait for the subscribers to be ready
    num_subscribers_ready = 0
    while num_subscribers_ready < num_subscribers:
        msg = mod.read_message(timeout=-1)
        if msg is not None:
            if msg.msg_name == 'SUBSCRIBER_READY':
                num_subscribers_ready += 1

    # Create TEST message with dummy data
    msg = pyrtma.Message('TEST')
    msg.data.data[:] = list(range(msg_size))

    # Send loop
    tic = time.perf_counter()
    for n in range(num_msgs):
        mod.send_message(msg)
    toc = time.perf_counter()

    # Stats
    dur = toc - tic
    data_rate = msg.msg_size * num_msgs / float(1048576) / dur
    print(f"Publisher[{pub_id}] -> {num_msgs} messages | {int(num_msgs/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")

    mod.disconnect()


def subscriber_loop(sub_id, num_msgs, msg_size, server='127.0.0.1:7111'):
    # Register user defined message types
    pyrtma.AddMessage(msg_name='TEST', msg_type=5000, msg_def=create_test_msg(msg_size))
    pyrtma.AddMessage(msg_name='SUBSCRIBER_READY', msg_type=5001, signal=True)

    # Setup Client
    mod = pyrtma.rtmaClient()
    mod.connect(server_name=server)
    mod.send_module_ready()
    mod.subscribe(['TEST', 'EXIT'])
    mod.send_signal('SUBSCRIBER_READY')

    # Read Loop (Start clock after first TEST msg received)
    abort_timeout = max(num_msgs/10000, 10) #seconds
    abort_start = time.perf_counter()

    msg_count = 0
    while msg_count < num_msgs:
        msg = mod.read_message(timeout=-1)
        if msg is not None:
            if msg.msg_name == 'TEST':
                if msg_count == 0:
                    test_msg_size = msg.msg_size
                    tic = time.perf_counter()
                toc = time.perf_counter()
                msg_count += 1
            elif msg.msg_name == 'EXIT':
                break
            
        if time.perf_counter() - abort_start > abort_timeout: 
            print(f"Subscriber [{sub_id:d}] Timed out.")
            break

    # Stats
    dur = toc - tic
    data_rate = (test_msg_size * num_msgs) / float(1048576) / dur
    if msg_count == num_msgs:
        print(f"Subscriber [{sub_id:d}] -> {msg_count} messages | {int((msg_count-1)/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")
    else:
        print(f"Subscriber [{sub_id:d}] -> {msg_count} ({int(msg_count/num_msgs *100):0d}%) messages | {int((msg_count-1)/dur)} messages/sec | {data_rate:0.1f} MB/sec | {dur:0.6f} sec ")

    mod.disconnect()


def create_test_msg(msg_size):
    class TEST(ctypes.Structure):
        _fields_ = [('data', ctypes.c_byte * msg_size)]
    return TEST


if __name__ == '__main__':
    import argparse

    # Configuration flags for bench utility
    parser = argparse.ArgumentParser(description='rtmaClient bench test utility')
    parser.add_argument('-ms', default=128, type=int, dest='msg_size', help='Messge size in bytes.')
    parser.add_argument('-n', default=100000, type=int, dest='num_msgs', help='Number of messages.')
    parser.add_argument('-np', default=1, type=int, dest='num_publishers', help='Number of concurrent publishers.')
    parser.add_argument('-ns', default=1, type=int, dest='num_subscribers', help='Number of concurrent subscribers.')
    parser.add_argument('-s',default='127.0.0.1:7111', dest='server', help='RTMA message manager ip address (default: 127.0.0.1:7111)')
    args = parser.parse_args()

    #Main Thread RTMA client
    mod = pyrtma.rtmaClient()
    mod.connect(server_name=args.server)
    mod.send_module_ready()

    print("Initializing publisher processses...")
    publisher_ready = []
    publishers = []
    for n in range(args.num_publishers):
        publisher_ready.append(multiprocessing.Event())
        publishers.append(
                multiprocessing.Process(
                    target=publisher_loop,
                    kwargs={
                        'pub_id': n+1,
                        'num_msgs': int(args.num_msgs/args.num_publishers),
                        'msg_size': args.msg_size, 
                        'num_subscribers': args.num_subscribers,
                        'ready_flag': publisher_ready[n],
                        'server': args.server})
                    )
        publishers[n].start()

    # Wait for publisher processes to be established
    for flag in publisher_ready:
        flag.wait()

    print('Waiting for subscriber processes...')
    subscribers = []
    for n in range(args.num_subscribers):
        subscribers.append(
                multiprocessing.Process(
                    target=subscriber_loop,
                    args=(n+1, args.num_msgs, args.msg_size),
                    kwargs={'server':args.server}))
        subscribers[n].start()

    print("Starting Test...")
    print(f"RTMA packet size: {pyrtma.constants['HEADER_SIZE'] + args.msg_size}")
    print(f'Sending {args.num_msgs} messages...')

    # Wait for publishers to finish
    for publisher in publishers:
        publisher.join()

    # Wait for subscribers to finish
    abort_timeout = max(args.num_msgs/10000, 10) #seconds
    abort_start = time.perf_counter()
    abort = False

    while not abort:
        subscribers_finished = 0
        for subscriber in subscribers:
            if subscriber.exitcode is not None:
                subscribers_finished += 1

        if subscribers_finished == len(subscribers):
            break

        if time.perf_counter() - abort_start > abort_timeout: 
            mod.send_signal('EXIT')
            print('Test Timeout! Sending Exit Signal...')
            abort = True

    for subscriber in subscribers:
        subscriber.join()
    
    print('Done!')
