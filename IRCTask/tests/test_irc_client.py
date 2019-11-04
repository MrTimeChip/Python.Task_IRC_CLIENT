from data_transfer.user import User
from client.irc_client import IRCClient


class TestIRCClient:

    def setup(self):
        self.client = IRCClient()

    def test_update_channels_list_makes_client_search_for_channels(self):
        self.client.update_channels_list()
        assert self.client.is_searching_for_channels is True

    def test_is_message_user_message_should_be_true_when_user_message(self):
        user_message = ':Macha!~macha@unaffiliated/macha PRIVMSG #botwar ' \
                       ':Test response '
        assert self.client.is_message_user_message(user_message) is True

    def test_establish_connection_should_change_status_empty_fields(self):
        self.client.connect_to_server('',
                                          6667)
        self.client.establish_connection()
        assert self.client.current_status == "E: NO FIELDS SHOULD BE EMPTY!"

    def test_establish_connection_should_change_status_wrong_server_name(self):
        self.client.set_user(User("Username1234321"))
        self.client.connect_to_server("E: WRONG SERVER NAME",
                                      6667)
        self.client.establish_connection()
        assert self.client.current_status == "E: WRONG SERVER NAME"
