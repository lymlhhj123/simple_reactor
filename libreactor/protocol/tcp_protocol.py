# coding: utf-8

from .. import const
from .protocol import Protocol


class TcpProtocol(Protocol):

    def connection_error(self, error: const.ConnectionErr):
        """

        :param error:
        :return:
        """

    def send_data(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
