import socket
import threading

from queue import Queue


class IRCSocket:

    def __init__(self):
        self.__server_data = '', 0
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.joined_channel = False
        self.connected_channel_name = "NONE"
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
            raise socket.timeout
        except socket.gaierror:
            raise ValueError
        except OSError:
            raise ValueError
        except Exception as e:
            raise e
        else:
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
            raise ValueError("Connect to server first!")

        self.__socket.send(bytes("JOIN {} \n".format(channel_name), "UTF-8"))
        self.joined_channel = True
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
            if not self.connected:
                break
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

    def get_users_list(self):
        self.send_message('NAMES ' + self.connected_channel_name)

    def is_message_queue_empty(self):
        return self._messages_queue.empty()

    def handle_message(self, message):
        print(message)
        if self.output_receiver is not None:
            self.output_receiver(message)

    def send_message(self, message):
        self._messages_queue.put(lambda: self.__socket.send(
            bytes(message + '\n', "UTF-8")))
        self.handle_message(message)

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
