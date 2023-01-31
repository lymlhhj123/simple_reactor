# coding: utf-8

from .protocol import Protocol


class TcpProtocol(Protocol):

    def send_data(self, data: bytes):
        """

        :param data:
        :return:
        """
        if not isinstance(data, bytes):
            return

        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
