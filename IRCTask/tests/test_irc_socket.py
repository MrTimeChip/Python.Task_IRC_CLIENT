import pytest
from client.irc_socket import IRCSocket


class TestIrcSocket:

    def setup(self):
        self.irc_socket = IRCSocket()

    def test_join_channel_throws_value_error_when_not_connected(self):
        with pytest.raises(ValueError):
            self.irc_socket.join_channel("all")

    def test_connect_to_server_successfully_connects(self):
        self.irc_socket.set_server_data('chat.freenode.net', 6667)
        self.irc_socket.connect_to_server()
        assert self.irc_socket.connected is True

    def test_connect_to_server_raises_value_error_on_incorrect_data(self):
        self.irc_socket.set_server_data('', 6667)
        with pytest.raises(ValueError):
            self.irc_socket.connect_to_server()

    def test_send_message_should_add_new_message_to_queue(self):
        self.irc_socket.send_message("new message")
        assert self.irc_socket.is_message_queue_empty() is False

    def test_get_channels_list_should_add_new_message_to_queue(self):
        self.irc_socket.get_channels_list()
        assert self.irc_socket.is_message_queue_empty() is False

    def test_get_users_list_should_add_new_message_to_queue(self):
        self.irc_socket.get_users_list()
        assert self.irc_socket.is_message_queue_empty() is False

    def test_ping_should_add_new_message_to_queue(self):
        self.irc_socket.get_users_list()
        assert self.irc_socket.is_message_queue_empty() is False

    def test_join_channel_should_join_channel(self):
        self.irc_socket.set_server_data('chat.freenode.net', 6667)
        self.irc_socket.connect_to_server()
        self.irc_socket.join_channel("#channel")
        assert self.irc_socket.joined_channel is True

    def test_disconnect_disconnects_when_connected(self):
        self.irc_socket.set_server_data('chat.freenode.net', 6667)
        self.irc_socket.connect_to_server()
        self.irc_socket.disconnect()
        assert self.irc_socket.connected is False

    def teardown(self):
        self.irc_socket.disconnect()
