import re
from irc_socket import IRCSocket
import threading as thr
from connection_data import ConnectionData
from channel_info import ChannelInfo
from user import User


class IRCClient:
    channel_regex = '.*? .*? .*? (.*?) (.*?) (.*)$'

    def __init__(self):
        self.__irc_socket = IRCSocket()
        self.connection_data = ConnectionData()
        self.connection_data.user = User("")
        self.last_message = '...'

        self.__new_channel_data = False

        self.__channel_compiled_regex = re.compile(self.channel_regex)

        self.__socket_thread = thr.Thread(target=self.establish_connection)
        self.__channel_thread = thr.Thread(target=self.__collect_channels)

        self.status_update_handler = None

        self.chat_handler = None
        self.channel_data_handler = None

        self.on_connected_to_server = None

    def establish_connection(self):
        if self.check_connection_data():
            self.__irc_socket.set_server_data(self.connection_data.server,
                                              self.connection_data.port)

            self.__irc_socket.output_receiver = self.handle_irc_message
            self.__irc_socket.connect_to_server()

            if self.__irc_socket.connected:
                self.__irc_socket.send_user_data(self.connection_data.user)
                if self.on_connected_to_server is not None:
                    self.on_connected_to_server()
        else:
            self.__socket_thread.join()

    def set_user(self, user):
        self.connection_data.user = user

    def send_user_message(self, message, target='def'):
        if target == "def":
            target = self.connection_data.channel
        message = "PRIVMSG {0} :{1}".format(target, message)
        self.__irc_socket.send_message(message)

    def check_connection_data(self):
        server_is_not_empty = (not self.connection_data.server == "")
        name_is_not_empty = (not self.connection_data.user.username == "")
        return server_is_not_empty and name_is_not_empty

    def handle_irc_message(self, text):
        self.last_message = text
        if self.status_update_handler is not None:
            self.status_update_handler(text)

        if text.find("PRIVMSG") != -1:
            if self.chat_handler is not None:
                self.chat_handler(text)

        if self.__irc_socket.is_searching_for_channels:
            self.__new_channel_data = True

    def connect_to_server(self, server_name, server_port):
        self.connection_data.server = server_name
        self.connection_data.port = server_port
        if self.__socket_thread.is_alive():
            return
        else:
            self.__socket_thread.start()

    def connect_to_channel(self, channel_name):
        self.__irc_socket.join_channel(channel_name)

    def disconnect(self):
        self.__irc_socket.disconnect()
        if self.__channel_thread.is_alive():
            self.__channel_thread.join()
        if self.__socket_thread.is_alive():
            self.__socket_thread.join()

    def update_channels_list(self):
        self.__channel_thread.start()
        self.__irc_socket.get_channels_list()

    def __collect_channels(self):
        while True:
            if self.__new_channel_data:
                channel_match = re.fullmatch(self.__channel_compiled_regex,
                                             self.last_message)

                if channel_match is None:
                    continue

                if channel_match.group(1).startswith(':End'):
                    self.__irc_socket.is_searching_for_channels = False
                    break

                channel_info = ChannelInfo(channel_match.group(1),
                                           channel_match.group(2),
                                           channel_match.group(3)[1:])
                if self.channel_data_handler is not None:
                    self.channel_data_handler(channel_info)
                self.__new_channel_data = False
