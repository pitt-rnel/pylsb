import unittest
from unittest.mock import Mock

from pyrtma.manager import MessageManager
from pyrtma.internal_types import Subscribe, Unsubscribe


class TestMessageManager(unittest.TestCase):
    def setUp(self):
        self.SUT = MessageManager()
        self.SUT.logger.disabled = True

    def tearDown(self):
        for mod in self.SUT.modules:
            mod.close()

    ########## Connect Module ##########

    # connect_module returns true on success
    def test_connect_module_returns_true_on_success(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        module_mock.conn = socket_mock

        # Act
        result = self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertTrue(
            result,
            msg="connect_module: True not returned on success",
        )

    # connect_module stores module in modules
    # def test_connect_module_stores_module_in_modules(self):
    #     # Arrange
    #     socket_mock = Mock()
    #     module_mock = Mock()
    #     message_mock = Mock()
    #     module_mock.conn = socket_mocks

    #     # Act
    #     self.SUT.connect_module(module_mock, message_mock)

    #     # Assert
    #     self.assertIsNotNone(self.SUT.modules.get(socket_mock))

    # connect_module returns false on module id reuse
    def test_connect_module_returns_false_on_module_id_reuse(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        module_mock.conn = socket_mock
        module_mock.id = 50
        message_mock.header.src_mod_id = 50
        self.SUT.modules[socket_mock] = module_mock

        # Act
        result = self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertFalse(
            result,
            msg="connect_module: False not returned on module id reuse",
        )

    # connect_module auto assigns module id
    def test_connect_module_auto_assigns_module_id(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        module_mock.conn = socket_mock
        module_mock.id = 0
        message_mock.header.src_mod_id = 0

        # Act
        self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertNotEqual(
            module_mock.id,
            0,
            msg="connect_module: Module id not auto assigned",
        )

    # connect_module assigns module specified id
    def test_connect_module_assigns_module_specified_id(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        module_mock.conn = socket_mock
        module_mock.id = 0
        message_mock.header.src_mod_id = 50

        # Act
        self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertEqual(
            module_mock.id,
            50,
            msg=f"connect_module: Module id not specified value 50",
        )

    # connect_module connects to module
    def test_connect_module_connects_to_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        module_mock.conn = socket_mock

        # Act
        self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertTrue(
            module_mock.connected,
            msg="connect_module: Module not connected",
        )

    # connect_module stores logger module
    def test_connect_module_stores_logger_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        message_mock = Mock()
        message_mock.data.logger_status = 1
        module_mock.conn = socket_mock

        # Act
        self.SUT.connect_module(module_mock, message_mock)

        # Assert
        self.assertTrue(
            module_mock in self.SUT.logger_modules,
            msg="connect_module: Logger module not stored",
        )

    ########## Remove Module ##########

    # remove_module removes module from stored modules
    def test_remove_module_removes_module_from_stored_modules(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock

        # Act
        self.SUT.remove_module(module_mock)

        # Assert
        self.assertIsNone(
            self.SUT.modules.get(socket_mock),
            msg="remove_module: Module not removed from stored modules",
        )

    # remove_module removes logger module
    def test_remove_module_removes_logger_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock
        self.SUT.logger_modules.add(module_mock)

        # Act
        self.SUT.remove_module(module_mock)

        # Assert
        self.assertTrue(
            module_mock not in self.SUT.logger_modules,
            msg="remove_module: Logger module not removed",
        )

    # remove_module calls close on module
    def test_remove_module_calls_close_on_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock

        # Act
        self.SUT.remove_module(module_mock)

        # Assert
        module_mock.close.assert_called_once()

    # remove_module removes module subscriptions
    def test_remove_module_removes_module_subscriptions(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock
        self.SUT.subscriptions[100] = set([module_mock])
        self.SUT.subscriptions[200] = set([module_mock])

        # Act
        self.SUT.remove_module(module_mock)

        # Assert
        self.assertTrue(
            module_mock not in self.SUT.subscriptions[100],
            msg="remove_module: Subscriptions not removed for module",
        )
        self.assertTrue(
            module_mock not in self.SUT.subscriptions[200],
            msg="remove_module: Subscriptions not removed for module",
        )

    ########## Disconnect Module ##########

    # disconnect_module removes module from stored modules
    def test_disconnect_module_removes_module_from_stored_modules(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock

        # Act
        self.SUT.disconnect_module(module_mock)

        # Assert
        self.assertIsNone(
            self.SUT.modules.get(socket_mock),
            msg="disconnect_module: Module not removed from stored modules",
        )

    # disconnect_module removes logger module
    def test_disconnect_module_removes_logger_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock
        self.SUT.logger_modules.add(module_mock)

        # Act
        self.SUT.disconnect_module(module_mock)

        # Assert
        self.assertTrue(
            module_mock not in self.SUT.logger_modules,
            msg="disconnect_module: Logger module not removed",
        )

    # disconnect_module calls close on module
    def test_disconnect_module_calls_close_on_module(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock

        # Act
        self.SUT.disconnect_module(module_mock)

        # Assert
        module_mock.close.assert_called_once()

    # disconnect_module removes module subscriptions
    def test_disconnect_module_removes_module_subscriptions(self):
        # Arrange
        socket_mock = Mock()
        module_mock = Mock()
        module_mock.conn = socket_mock
        self.SUT.modules[socket_mock] = module_mock
        self.SUT.subscriptions[100] = set([module_mock])
        self.SUT.subscriptions[200] = set([module_mock])

        # Act
        self.SUT.disconnect_module(module_mock)

        # Assert
        self.assertTrue(
            module_mock not in self.SUT.subscriptions[100],
            msg="disconnect_module: Subscriptions not removed for module",
        )
        self.assertTrue(
            module_mock not in self.SUT.subscriptions[200],
            msg="disconnect_module: Subscriptions not removed for module",
        )

    ########## Add Subscription ##########

    # add subscription stores subscription
    def test_add_subscription_stores_subscription(self):
        # Arrange
        module_mock = Mock()
        msg_mock = Mock()
        msg_mock.data = Subscribe(msg_type=50)

        # Act
        self.SUT.add_subscription(module_mock, msg_mock)

        # Assert
        self.assertTrue(
            module_mock in self.SUT.subscriptions[50],
            msg="add_subscription: Subscription not stored",
        )

    ########## Remove Subscription ##########

    # remove subscription removes subscription from stored subscriptions
    def test_remove_subscription_removes_subscription(self):
        # Arrange
        module_mock = Mock()
        msg_mock = Mock()
        msg_mock.data = Unsubscribe(msg_type=50)
        self.SUT.subscriptions[50] = set([module_mock])

        # Act
        self.SUT.remove_subscription(module_mock, msg_mock)

        # Assert
        self.assertTrue(
            module_mock not in self.SUT.subscriptions[50],
            msg="remove_subscription: Subscription not removed from subscriptions",
        )
