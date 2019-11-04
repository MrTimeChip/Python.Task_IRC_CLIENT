import re
from client.irc_socket import IRCSocket
import threading as thr
from data_transfer.connection_data import ConnectionData
from data_transfer.channel_info import ChannelInfo
from data_transfer.user import User
from data_transfer.transmitter import Transmitter


class IRCClient:
    CHANNEL_REGEX = r'.*? .*? .*? ([^:].*?) (\d.*?) (:.*)$'
    MESSAGE_SPLITTING_REGEX = r'.*? :(.*?$)'

    def __init__(self):
        self.__irc_socket = IRCSocket()
        self.connection_data = ConnectionData()
        self.connection_data.user = User("")

        self.current_status = ""

        self.is_searching_for_channels = False
        self.is_searching_for_names = False

        self.__channel_compiled_regex = re.compile(
            IRCClient.CHANNEL_REGEX)

        self.__message_splitting_compiled_regex = re.compile(
            IRCClient.MESSAGE_SPLITTING_REGEX)

        self.__socket_thread = thr.Thread(target=self.__connect_socket)

        self.status_update_handler = Transmitter()

        self.chat_transmitter = Transmitter()
        self.channel_names_transmitter = Transmitter()
        self.channel_data_handler = Transmitter()

        self.on_connected_to_server = None

    def establish_connection(self):
        if self.__irc_socket.connected:
            self.disconnect()
        if self.check_connection_data():
            self.__connect_socket()
        else:
            if self.__socket_thread.is_alive():
                self.__socket_thread.join()
            self.update_status("E: NO FIELDS SHOULD BE EMPTY!")

    def __connect_socket(self):
        self.update_status("N: CONNECTING...")
        self.__irc_socket.set_server_data(self.connection_data.server,
                                          self.connection_data.port)

        self.__irc_socket.output_receiver = self.handle_irc_message
        try:
            self.__irc_socket.connect_to_server()
        except ValueError:
            self.update_status("E: WRONG SERVER NAME")
        except Exception as e:
            raise e
        else:
            self.update_status("S: SUCCESSFULLY CONNECTED")

        if self.__irc_socket.connected:
            self.__irc_socket.send_user_data(self.connection_data.user)
            if self.on_connected_to_server is not None:
                self.on_connected_to_server()

    def set_user(self, user):
        self.connection_data.user = user

    def is_message_user_message(self, message):
        return self.is_in_message_preamble(message, "PRIVMSG")

    def is_in_message_preamble(self, message, pattern):
        message_match = re.match(self.__message_splitting_compiled_regex,
                                 message)
        if message_match is None:
            return False
        message_preamble = message_match.group(0)
        return message_preamble.find(pattern) != -1

    def send_user_message(self, message, target='def'):
        if target == "def":
            target = self.connection_data.channel
        message = "PRIVMSG {0} :{1}".format(target, message)
        self.__irc_socket.send_message(message)

    def check_connection_data(self):
        server_is_not_empty = (not self.connection_data.server == "")
        name_is_not_empty = (not self.connection_data.user.username == "")
        return server_is_not_empty and name_is_not_empty

    def update_status(self, text):
        self.current_status = text
        if self.status_update_handler.can_transmit():
            self.status_update_handler.transmit(text)

    def handle_irc_message(self, text):  # pragma: no cover
        if self.is_message_user_message(text):
            if self.__irc_socket.joined_channel:
                if self.chat_transmitter.can_transmit():
                    self.chat_transmitter.transmit(text)
                return
        else:
            if self.is_searching_for_names and \
                    self.is_message_names_list(text) != -1:
                if self.channel_names_transmitter.can_transmit():
                    self.channel_names_transmitter.transmit(text)
                return
            if text.find("JOIN") != -1 and text.find(
                    self.__irc_socket.connected_channel_name) != -1:
                self.is_searching_for_names = True
                return
            if self.is_searching_for_channels:
                self.__collect_channels(text)

    def is_message_names_list(self, message):
        preamble_type_1 = "@ " + self.__irc_socket.connected_channel_name
        preamble_type_2 = "= " + self.__irc_socket.connected_channel_name
        return self.is_in_message_preamble(message, preamble_type_1) or \
               self.is_in_message_preamble(message, preamble_type_2)

    def connect_to_server(self, server_name, server_port):
        self.connection_data.server = server_name
        self.connection_data.port = server_port
        if self.__socket_thread.is_alive():
            return
        else:
            self.__socket_thread.start()

    def connect_to_channel(self, channel_name):
        self.connection_data.channel = channel_name
        self.__irc_socket.join_channel(channel_name)

    def disconnect(self):
        self.__irc_socket.disconnect()
        if self.__socket_thread.is_alive():
            self.__socket_thread.join()

    def update_channels_list(self):
        self.__irc_socket.get_channels_list()
        self.is_searching_for_channels = True

    def __collect_channels(self, channel_data):
        channel_match = re.fullmatch(self.__channel_compiled_regex,
                                     channel_data)

        if channel_match is None:
            return

        if channel_match.group(1).startswith('Channel'):
            return

        if channel_match.group(1).startswith(':End'):
            self.is_searching_for_channels = False

        channel_info = ChannelInfo(channel_match.group(1),
                                   channel_match.group(2),
                                   channel_match.group(3)[1:])
        if self.channel_data_handler.can_transmit():
            self.channel_data_handler.transmit(channel_info)
