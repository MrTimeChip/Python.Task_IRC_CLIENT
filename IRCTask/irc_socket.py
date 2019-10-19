import socket
import threading

from queue import Queue


class IRCSocket:

    def __init__(self, server_name, server_port):
        self.server_data = server_name, server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.connected_channel_name = "NONE"
        self.is_searching_for_channels = False
        self.messages_queue = Queue()
        self.output_receiver = None
        self.reading_thread = None
        self.writing_thread = None
        self.user = None

    def connect_to_server(self):
        try:
            self.socket.connect(self.server_data)
        except socket.timeout:
            raise socket.timeout
        else:
            self.connected = True

    def send_user_data(self, user):
        self.socket.send(bytes("USER {0} {0} {0} {1} \n"
                               .format(user.username, user.real_name),
                               "UTF-8"))
        self.socket.send(bytes("NICK {} \n".format(user.username), "UTF-8"))

    def join_channel(self, channel_name):
        self.socket.send(bytes("JOIN {} \n".format(channel_name), "UTF-8"))
        irc_message = ""
        buffer = ''
        while irc_message.find("End of /NAMES list.") == -1:
            irc_message = self.socket.recv(2048).decode("UTF-8")
            buffer += irc_message
            newline_pos = buffer.find('\r\n')
            if not newline_pos == -1:
                message_part = buffer[:newline_pos]
                buffer = buffer[newline_pos + 2:]
                self.handle_message(message_part)
        self.connected_channel_name = channel_name

    def start_session(self, channel_name, user):
        self.user = user
        self.connect_to_server()
        self.send_user_data(user)
        if not channel_name == '':
            self.join_channel(channel_name)

        self.reading_thread = threading.Thread(target=self.read_messages)
        self.reading_thread.start()
        self.writing_thread = threading.Thread(target=self.write_messages)
        self.writing_thread.start()
        self.get_channels_list()

    def write_messages(self):
        while self.connected:
            if not self.messages_queue.empty():
                self.messages_queue.get()()

    def read_messages(self):
        buffer = ''
        while self.connected:
            irc_message = self.socket.recv(2048).decode("UTF-8",
                                                        errors='replace')
            buffer += irc_message
            messages = buffer.split('\r\n')
            for raw_message in messages[:-1]:
                self.handle_message(raw_message)
                if raw_message.find("PING :") != -1:
                    self.ping()
            buffer = ''
            buffer += messages[-1]
            self.reading_thread.sleep(1)

    def get_channels_list(self):
        self.send_message('LIST')
        self.is_searching_for_channels = True

    def handle_message(self, message):
        print(message)
        if self.output_receiver is not None:
            self.output_receiver(message)

    def send_message(self, message):
        self.messages_queue.put(lambda: self.socket.send(
            bytes(message + "\n", "UTF-8")))

    def ping(self):
        self.send_message("PONG :pingisn")

    def disconnect(self):
        if self.connected:
            self.send_message("QUIT")
            self.connected = False
        if self.reading_thread.is_alive():
            self.reading_thread.join()
        if self.writing_thread.is_alive():
            self.writing_thread.join()
