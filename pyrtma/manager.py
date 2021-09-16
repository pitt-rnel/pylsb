import argparse
import logging


class Subscription:
    pass


class MessageManager:
    def __init__(self, server_ip: str, port: int):
        pass

    def send_message(self):
        """Sends a message to a module, specifying the MessageManager itself as the source module."""
        pass

    def send_signal(self):
        pass

    def send_ack(self):
        pass

    def process_message(self):
        pass

    def forward_message(self):
        """ Forward a message from other modules
        The given message will be forwarded to:
            - all subscribed logger modules (ALWAYS)
            - if the message has a destination address, and it is subscribed to by that destination it will be forwarded only there
            - if the message has no destination address, it will be forwarded to all subscribed modules
        """
        pass

    def dispatch_message(self):
        pass

    def connect_module(self):
        pass

    def disconnect_module(self):
        pass

    def add_subscription(self):
        pass

    def remove_subscription(self):
        pass

    def resume_subscription(self):
        pass

    def pause_subscription(self):
        pass

    def run(self):
        while True:
            # Listen for new client connections
            # Add new clients to client list
            # Poll client sockets using select to see which have data.
            # Distribute messages
            pass


if __name__ == "__main__":

    msg_mgr = MessageManager("127.0.0.1", 7111)

    msg_mgr.run()
