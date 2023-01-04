# coding: utf-8

from .protocol import Protocol


class Stream(Protocol):

    def safe_send_data(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
        self.event_loop.call_soon(self.send_data, data)

    def send_data(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
        self.connection.write(data)

    def data_received(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
