import pytest
from data_transfer.transmitter import Transmitter


def receiver(data):
    print(data)


class TestTransmitter:
    def setup(self):
        self.transmitter = Transmitter()

    def test_can_transmit_when_receiver_is_connected(self):
        self.transmitter.connect_receiver(receiver)
        assert self.transmitter.can_transmit() is True

    def test_transmit_raises_value_error_when_no_receiver_connected(self):
        with pytest.raises(ValueError):
            self.transmitter.transmit("data")

    def test_is_transmitted_any_data_is_true_when_transmitted_once(self):
        self.transmitter.connect_receiver(receiver)
        self.transmitter.transmit("data")
        assert self.transmitter.is_transmitted_any_data() is True
