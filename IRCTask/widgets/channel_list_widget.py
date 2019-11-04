import PyQt5.QtWidgets as QtWidgets


class ChannelsListWidget(QtWidgets.QListWidget): # pragma: no cover

    def __init__(self):
        super(ChannelsListWidget, self).__init__()
        self.joining_delegate = None

    def set_joining_delegate(self, joining_delegate):
        self.joining_delegate = joining_delegate

    def check_joining_delegate(self):
        return self.joining_delegate is not None

    def connect_to_channel(self, item):
        if self.check_joining_delegate():
            self.joining_delegate(item.data(256).name)
        else:
            raise ValueError("Joining delegate is None!")
