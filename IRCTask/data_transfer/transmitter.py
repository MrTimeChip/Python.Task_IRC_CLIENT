class Transmitter:

    def __init__(self):
        self.receiver = None
        self.__transmitted_any_data = False

    def transmit(self, data):
        if self.can_transmit():
            self.__transmitted_any_data = True
            self.receiver(data)
        else:
            raise ValueError('No transmitter delegate is set!')

    def connect_receiver(self, receiver_delegate):
        self.receiver = receiver_delegate

    def can_transmit(self):
        return self.receiver is not None

    def is_transmitted_any_data(self):
        return self.__transmitted_any_data