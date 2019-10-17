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
        self.message_output_receiver = None
        self.debug_output_receiver = None
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
        while irc_message.find("End of /NAMES list.") == -1:
            irc_message = self.socket.recv(2048).decode("UTF-8")
            irc_message = irc_message.strip('\n\r')
            self.handle_debug_message(irc_message)
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
        while self.connected:
            irc_message = self.socket.recv(2048).decode("UTF-8",
                                                        errors='replace')
            irc_message = irc_message.strip('\n\r')
            self.handle_debug_message(irc_message)
            if irc_message.find("PRIVMSG") != -1:
                name = irc_message.split('!', 1)[0][1:]
                message = irc_message.split('PRIVMSG', 1)[1].split(':', 1)[1]
                self.handle_message(name, message)
            if irc_message.find("PING :") != -1:
                self.ping()

    def get_channels_list(self):
        self.send_command_message('LIST')
        self.is_searching_for_channels = True

    def handle_message(self, name, message):
        if self.message_output_receiver is not None:
            self.message_output_receiver("{0}: {1}".format(name, message))

    def handle_debug_message(self, message):
        print(message)
        if self.debug_output_receiver is not None:
            self.debug_output_receiver(message)

    def send_message_to_chat(self, message, target="def"):
        if target == "def":
            target = self.connected_channel_name
        if message.startswith('/'):
            self.send_command_message(message[1:])
            return
        self.messages_queue.put(lambda: self.socket.send(
            bytes("PRIVMSG {0} :{1}\n".format(target, message), "UTF-8")))
        self.handle_message(self.user.username, message)

    def send_command_message(self, message):
        self.messages_queue.put(lambda: self.socket.send(bytes(message + "\n",
                                                               "UTF-8")))

    def ping(self):
        self.socket.send(bytes("PONG :pingisn", "UTF-8"))

    def disconnect(self):
        self.connected = False
        self.send_command_message("QUIT")
        self.reading_thread.join()
        self.writing_thread.join()
