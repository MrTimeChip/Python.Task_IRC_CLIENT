from client.irc_client import IRCClient
from widgets.channel_list_widget import ChannelsListWidget
import queue
import threading
import PyQt5.QtWidgets as QtWidgets
from data_transfer.user import User
import re


class MainWidget(QtWidgets.QWidget):  # pragma: no cover

    NAMES_REGEX = r".*? (@|=) .*? :(.*?$)"
    USERS_PREFIXES_WEIGHT = {
        "~": 1,
        "&": 2,
        "@": 3,
        "%": 4,
        "+": 5
    }
    STATUS_TYPES_COLOR = {
        "N": "black",
        "E": "red",
        "S": "green"
    }

    def __init__(self):
        super().__init__()
        self.__irc_client = IRCClient()

        self.__irc_client.chat_transmitter.connect_receiver(
            self.receive_chat_text)

        self.__irc_client.channel_names_transmitter.connect_receiver(
            self.receive_names)

        self.__irc_client.status_update_handler.connect_receiver(
            self.update_status_widget)

        self.__irc_client.channel_data_handler.connect_receiver(
            self.handle_channels_list)

        self.__irc_client.on_connected_to_server = self.on_connected_to_server

        self.__channels_list_thread = threading.Thread(
            target=self.__fill_channels_list)
        self.__channels_info_queue = queue.Queue()

        self.connect_button = QtWidgets.QPushButton('Connect', self)
        self.join_button = QtWidgets.QPushButton('Join', self)
        self.send_button = QtWidgets.QPushButton('Send', self)
        self.search_button = QtWidgets.QPushButton('Search', self)

        self.__chat_text_widget = QtWidgets.QTextEdit()
        self.__server_name_widget = QtWidgets.QLineEdit()
        self.__channel_name_widget = QtWidgets.QLineEdit()
        self.__username_widget = QtWidgets.QLineEdit()
        self.__chat_input_widget = QtWidgets.QLineEdit()
        self.__channels_list_widget = ChannelsListWidget()
        self.__channels_list_widget.set_joining_delegate(
            self.__irc_client.connect_to_channel)
        self.__users_list_widget = QtWidgets.QListWidget()
        self.__status_widget = QtWidgets.QLabel()

        self.initialize_ui()

    def initialize_ui(self):
        grid = self.create_grid()

        self.setLayout(grid)

        self.__channels_list_widget.itemDoubleClicked.connect(
            self.__channels_list_widget.connect_to_channel
        )

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Chat")
        self.show()

    def create_grid(self):
        server_name_label = QtWidgets.QLabel('Server')
        channel_join_label = QtWidgets.QLabel('Join by name:')
        username_label = QtWidgets.QLabel('Username')
        channels_list_label = QtWidgets.QLabel('Channels:')
        users_list_label = QtWidgets.QLabel('Users')

        self.connect_button.setToolTip('Establish connection')
        self.connect_button.clicked.connect(self.connect_to_server)

        self.join_button.setToolTip('Join channel by name')
        self.join_button.setDisabled(True)
        self.join_button.clicked.connect(self.connect_to_channel)

        self.send_button.setToolTip('Send a message')
        self.send_button.clicked.connect(self.send_user_message)

        self.search_button.setToolTip('Search for channels on the server')
        self.search_button.setFixedSize(60, 25)
        self.search_button.setDisabled(True)
        self.search_button.clicked.connect(self.update_channels_list)

        self.__chat_text_widget.setMinimumSize(400, 500)
        self.__chat_text_widget.setReadOnly(True)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(7)

        grid.addWidget(server_name_label, 1, 0)
        grid.addWidget(self.__server_name_widget, 1, 1)

        grid.addWidget(channel_join_label, 6, 0)
        grid.addWidget(self.join_button, 7, 0)
        grid.addWidget(self.__channel_name_widget, 7, 1)

        grid.addWidget(username_label, 3, 0)
        grid.addWidget(self.__username_widget, 3, 1)
        grid.addWidget(self.connect_button, 4, 0)

        grid.addWidget(channels_list_label, 5, 0)
        grid.addWidget(self.search_button, 5, 1)
        grid.addWidget(self.__channels_list_widget, 6, 1)

        grid.addWidget(self.__chat_text_widget, 1, 4, 6, 2)
        grid.addWidget(self.send_button, 7, 4, 1, 1)
        grid.addWidget(self.__chat_input_widget, 7, 5, 1, 1)

        grid.addWidget(users_list_label, 1, 7)
        grid.addWidget(self.__users_list_widget, 2, 7, 5, 3)

        grid.addWidget(self.__status_widget, 9, 0, 1, 5)

        return grid

    def receive_chat_text(self, text):
        if text.startswith(":"):
            name = text.split('!', 1)[0][1:]
            split_message = text.split('PRIVMSG', 1)
            message = split_message[1].split(':', 1)[1]
        else:
            name = self.__irc_client.connection_data.user.username
            message_start_index = text.find(":")
            message = text[message_start_index + 1:]
        self.__chat_text_widget.append('{0}: {1}'.format(name, message))

    def receive_names(self, text):
        names_match = re.match(MainWidget.NAMES_REGEX, text)
        if names_match is None:
            print("No names found!")
            return

        names = names_match.group(2)
        names_list = names.split()
        names_list = sorted(names_list,
                            key=lambda username:
                            self.prefixes_compare(username))
        for name in names_list:
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText(name)
            self.__users_list_widget.addItem(list_item)
        self.__irc_client.is_searching_for_names = False

    def update_channels_list(self):
        if self.__channels_list_thread.is_alive():
            self.__channels_list_thread.join()
        self.__channels_list_widget.clear()
        self.__channels_info_queue = queue.Queue()
        self.__irc_client.update_channels_list()
        self.__channels_list_thread.start()

    def prefixes_compare(self, username):
        if username[0] in self.USERS_PREFIXES_WEIGHT:
            return self.USERS_PREFIXES_WEIGHT[username[0]]
        else:
            return len(self.USERS_PREFIXES_WEIGHT) + 1

    def handle_channels_list(self, channel_info):
        if self.__irc_client.is_searching_for_channels:
            self.__channels_info_queue.put(channel_info)
        elif self.__channels_list_thread.is_alive():
            self.__channels_list_thread.join()

    def __fill_channels_list(self):
        while True:
            if not self.__channels_info_queue.empty():
                channel_info = self.__channels_info_queue.get()
                list_item = QtWidgets.QListWidgetItem()
                list_item.setData(256, channel_info)
                list_item.setText(channel_info.full_name)
                list_item.setToolTip("{0}\nUsers: {1}"
                                     .format(channel_info.name,
                                             channel_info.users_count))
                self.__channels_list_widget.addItem(list_item)

    def update_status_widget(self, text):
        status_data = text.split(" ", 1)
        status_type = status_data[0][0]
        status_text = status_data[1]
        status_color = self.STATUS_TYPES_COLOR[status_type]
        self.__status_widget.setStyleSheet("color: " + status_color + ";")
        self.__status_widget.setText(status_text)

    def on_connected_to_server(self):
        self.join_button.setEnabled(True)
        self.search_button.setEnabled(True)

    def send_user_message(self):
        message = self.__chat_input_widget.text()
        self.__chat_input_widget.clear()
        self.__irc_client.send_user_message(message)

    def connect_to_server(self):
        self.clear_widgets()
        self.__irc_client.set_user(User(self.__username_widget.text()))
        self.__irc_client.connect_to_server(self.__server_name_widget.text(),
                                            6667)

    def connect_to_channel(self):
        self.__irc_client.connect_to_channel(self.__channel_name_widget.text())

    def clear_widgets(self):
        self.__users_list_widget.clear()
        self.__channels_list_widget.clear()
        self.__chat_text_widget.clear()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,
                                               'Warning',
                                               "Are you sure to quit?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.__irc_client.disconnect()
            event.accept()
        else:
            event.ignore()
