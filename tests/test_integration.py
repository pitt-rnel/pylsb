import threading
import time
import unittest

from pylsb.client import Client
from pylsb.manager import MessageManager


class TestRunning(unittest.TestCase):
    def setUp(self):
        self.manager = MessageManager(
            ip_address="127.0.0.1",
            port=7111,
            timecode=False,
            debug=False,
            send_msg_timing=True,
        )
        self.manager_thread = threading.Thread(target=self.manager.run,)
        self.manager_thread.start()
        time.sleep(0.1)

    def tearDown(self):
        self.manager.close()
        self.manager_thread.join()
        for mod in self.manager.modules:
            mod.close()

    def test_whenClientConnect_clientConnectsToMessageManager(self):
        # Arrange
        client = Client(module_id=0, host_id=0, timecode=False)

        # Act
        client.connect(server_name="127.0.0.1:7111")
        time.sleep(0.1)

        # Assert
        self.assertTrue(client.connected, msg="Client not connected")
        self.assertEqual(
            2,
            len(self.manager.modules),
            msg="Module not found in Messager Manager modules",
        )
