import socket
import threading

from queue import Queue


class IRCSocket:

    def __init__(self):
        self.__server_data = '', 0
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.connected_channel_name = "NONE"
        self.is_searching_for_channels = False
        self._messages_queue = Queue()
        self.output_receiver = None
        self.__reading_thread = threading.Thread(target=self.read_messages)
        self.__writing_thread = threading.Thread(target=self.write_messages)
        self.user = None

    def set_server_data(self, server_name, server_port):
        self.__server_data = server_name, server_port

    def connect_to_server(self):
        try:
            self.__socket.connect(self.__server_data)
        except socket.timeout:
            print('Socket timeout exception!')
            raise socket.timeout
        except BaseException as e:
            raise e
        else:
            print('Connected')
            self.connected = True
            self.__reading_thread.start()
            self.__writing_thread.start()

    def send_user_data(self, user):
        self.user = user
        self.__socket.send(bytes("USER {0} {0} {0} {1} \n"
                                 .format(user.username, user.real_name),
                                 "UTF-8"))
        self.__socket.send(bytes("NICK {} \n".format(user.username), "UTF-8"))

    def join_channel(self, channel_name):
        if not self.connected:
            print('Connect to server first!')
            return
        self.__socket.send(bytes("JOIN {} \n".format(channel_name), "UTF-8"))
        irc_message = ""
        buffer = ''
        while irc_message.find("End of /NAMES list.") == -1:
            irc_message = self.__socket.recv(2048).decode("UTF-8")
            buffer += irc_message
            newline_pos = buffer.find('\r\n')
            if not newline_pos == -1:
                message_part = buffer[:newline_pos]
                buffer = buffer[newline_pos + 2:]
                self.handle_message(message_part)
        self.connected_channel_name = channel_name

    def write_messages(self):
        while self.connected:
            if not self._messages_queue.empty():
                self._messages_queue.get()()

    def read_messages(self):
        buffer = ''
        while self.connected:
            irc_message = self.__socket.recv(2048).decode("UTF-8",
                                                          errors='replace')
            buffer += irc_message
            messages = buffer.split('\r\n')
            for raw_message in messages[:-1]:
                self.handle_message(raw_message)
                if raw_message.find("PING :") != -1:
                    self.ping()
            buffer = ''
            buffer += messages[-1]

    def get_channels_list(self):
        self.send_message('LIST')
        self.is_searching_for_channels = True

    def get_users_list(self):
        self.send_message('NAMES ' + self.connected_channel_name)

    def handle_message(self, message):
        print(message)
        if self.output_receiver is not None:
            self.output_receiver(message)

    def send_message(self, message):
        self._messages_queue.put(lambda: self.__socket.send(
            bytes(message + "\n", "UTF-8")))

    def ping(self):
        self.send_message("PONG :pingisn")

    def disconnect(self):
        if self.connected:
            self.send_message("QUIT")
            self.connected = False
        if self.__reading_thread.is_alive():
            self.__reading_thread.join()
        if self.__writing_thread.is_alive():
            self.__writing_thread.join()
