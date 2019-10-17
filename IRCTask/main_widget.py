import threading
import PyQt5.QtWidgets as qt_widgets
from irc_socket import IRCSocket
from user import User
from connection_data import ConnectionData
from channel_info import ChannelInfo
import re


class MainWidget(qt_widgets.QWidget):

    channel_info_regex = '.*? .*? .*? (.*?) (.*?) (.*)$'

    def __init__(self):
        super().__init__()
        self.irc_socket = IRCSocket("", 0)
        self.user = User("")
        self.connection_data = ConnectionData("", "", "", User(""))

        self.chat_text_widget = qt_widgets.QTextEdit()
        self.server_name_widget = qt_widgets.QLineEdit()
        self.channel_name_widget = qt_widgets.QLineEdit()
        self.username_widget = qt_widgets.QLineEdit()
        self.chat_input_widget = qt_widgets.QLineEdit()
        self.channels_list_widget = qt_widgets.QListWidget()
        self.status_widget = qt_widgets.QLabel()

        self.channels_info = []

        self.socket_thread = threading.Thread(target=self.establish_connection)

        self.channel_info_compiled_regex = re.compile(self.channel_info_regex)

        self.initialize_ui()

    def initialize_ui(self):
        grid = self.create_grid()

        self.setLayout(grid)

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Chat")
        self.show()

    def create_grid(self):

        server_name_label = qt_widgets.QLabel('Server')
        channel_name_label = qt_widgets.QLabel('Channel')
        username_label = qt_widgets.QLabel('Username')
        channels_list_label = qt_widgets.QLabel('Channels:')

        connect_button = qt_widgets.QPushButton('Connect', self)
        connect_button.setToolTip('Establish connection')
        connect_button.clicked.connect(self.start_connection_thread)

        send_button = qt_widgets.QPushButton('Send', self)
        send_button.setToolTip('Send a message')
        send_button.clicked.connect(self.send_user_message)

        self.status_widget.setFixedSize(500, 10)
        self.chat_text_widget.setReadOnly(True)

        grid = qt_widgets.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(server_name_label, 1, 0)
        grid.addWidget(self.server_name_widget, 1, 1)
        grid.addWidget(channel_name_label, 2, 0)
        grid.addWidget(self.channel_name_widget, 2, 1)
        grid.addWidget(username_label, 3, 0)
        grid.addWidget(self.username_widget, 3, 1)
        grid.addWidget(connect_button, 4, 0)

        grid.addWidget(channels_list_label, 5, 1)
        grid.addWidget(self.channels_list_widget, 6, 1)

        grid.addWidget(self.chat_text_widget, 1, 2, 6, 2)
        grid.addWidget(send_button, 7, 2, 1, 1)
        grid.addWidget(self.chat_input_widget, 7, 3, 1, 1)

        grid.addWidget(self.status_widget, 8, 0, 1, 3)

        return grid

    def append_chat_text(self, text):
        self.chat_text.append(text)

    def append_debug_text(self, text):
        self.status_widget.setText(text)
        if self.irc_socket.is_searching_for_channels:
            self.collect_channels_info(text)

    def collect_channels_info(self, text):
        text = text.split('\n')
        for channel in text:
            channel_info_match = re.fullmatch(self.channel_info_compiled_regex,
                                              channel)
            if channel_info_match is None or \
               channel_info_match.group(1) == 'Channel':
                return

            if channel_info_match.group(1).startswith(':End'):
                self.irc_socket.is_searching_for_channels = False
                self.fill_channels_list()
                return

            channel_info = ChannelInfo(channel_info_match.group(1),
                                       channel_info_match.group(2),
                                       channel_info_match.group(3)[1:])
            self.channels_info.append(channel_info)

    def fill_channels_list(self):
        for channel_info in self.channels_info:
            list_item = qt_widgets.QListWidgetItem()
            list_item.setData(0, channel_info)
            list_item.setText(channel_info.full_name)
            list_item.setToolTip("{0}\nUsers: {1}"
                                 .format(channel_info.name,
                                         channel_info.users_count))
            self.channels_list_widget.addItem(list_item)

    def send_user_message(self):
        text = self.chat_input.text()
        self.chat_input.clear()
        self.irc_socket.send_message_to_chat(text)

    def start_connection_thread(self):
        if self.socket_thread.is_alive():
            return
        else:
            self.socket_thread.start()

    def establish_connection(self):
        self.connection_data = \
            ConnectionData(self.server_name_widget.text(),
                           6667,
                           self.channel_name_widget.text(),
                           User(self.username_widget.text()))

        if self.check_connection_data():
            self.irc_socket = IRCSocket(self.connection_data.server,
                                        self.connection_data.port)

            self.irc_socket.message_output_receiver = self.append_chat_text
            self.irc_socket.debug_output_receiver = self.append_debug_text

            self.irc_socket.start_session(self.connection_data.channel,
                                          self.connection_data.user)
        else:
            self.socket_thread.join()

    def check_connection_data(self):
        server_is_not_empty = (not self.connection_data.server == "")
        name_is_not_empty = (not self.connection_data.user.username == "")
        return server_is_not_empty and name_is_not_empty

    def closeEvent(self, event):
        reply = qt_widgets.QMessageBox.question(self,
                                                'Warning',
                                                "Are you sure to quit?",
                                                qt_widgets.QMessageBox.Yes |
                                                qt_widgets.QMessageBox.No,
                                                qt_widgets.QMessageBox.No)
        if reply == qt_widgets.QMessageBox.Yes:
            self.irc_socket.disconnect()
            if self.socket_thread.is_alive():
                self.socket_thread.join()
            event.accept()
        else:
            event.ignore()
