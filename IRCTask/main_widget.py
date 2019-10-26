from irc_client import IRCClient
import PyQt5.QtWidgets as QtWidgets
from user import User


class MainWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.__irc_client = IRCClient()
        self.__irc_client.chat_handler = self.handle_chat_text
        self.__irc_client.status_update_handler = self.update_status_widget
        self.__irc_client.channel_data_handler = self.handle_channel_list
        self.__irc_client.on_connected_to_server = self.on_connected_to_server

        self.connect_button = QtWidgets.QPushButton('Connect', self)
        self.join_button = QtWidgets.QPushButton('Join', self)
        self.send_button = QtWidgets.QPushButton('Send', self)
        self.search_button = QtWidgets.QPushButton('Search', self)

        self.__chat_text_widget = QtWidgets.QTextEdit()
        self.__server_name_widget = QtWidgets.QLineEdit()
        self.__channel_name_widget = QtWidgets.QLineEdit()
        self.__username_widget = QtWidgets.QLineEdit()
        self.__chat_input_widget = QtWidgets.QLineEdit()
        self.__channels_list_widget = QtWidgets.QListWidget()
        self.__users_list_widget = QtWidgets.QListWidget()
        self.__status_widget = QtWidgets.QLabel()

        self.initialize_ui()

    def initialize_ui(self):
        grid = self.create_grid()

        self.setLayout(grid)

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

        #grid.addWidget(self.__status_widget, 9, 0)

        return grid

    def handle_chat_text(self, text):
        name = text.split('!', 1)[0][1:]
        split_message = text.split('PRIVMSG', 1)
        message = split_message[1].split(':', 1)[1]
        self.__chat_text_widget.append('{0}: {1}'.format(name, message))

    def update_channels_list(self):
        self.__irc_client.update_channels_list()

    def handle_channel_list(self, channel_info):
        list_item = QtWidgets.QListWidgetItem()
        list_item.setData(0, channel_info)
        list_item.setText(channel_info.full_name)
        list_item.setToolTip("{0}\nUsers: {1}"
                             .format(channel_info.name,
                                     channel_info.users_count))
        self.__channels_list_widget.addItem(list_item)

    def update_status_widget(self, text):
        self.__status_widget.setText(text)

    def on_connected_to_server(self):
        self.join_button.setEnabled(True)
        self.search_button.setEnabled(True)

    def send_user_message(self):
        message = self.chat_input.text()
        self.chat_input.clear()
        self.__irc_client.send_user_message(message)

    def connect_to_server(self):
        self.__irc_client.set_user(User(self.__username_widget.text()))
        self.__irc_client.connect_to_server(self.__server_name_widget.text(),
                                            6667)
        if self.__channel_name_widget.text() != '':
            self.connect_to_channel()

    def connect_to_channel(self):
        self.__irc_client.connect_to_channel(self.__channel_name_widget.text())

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
