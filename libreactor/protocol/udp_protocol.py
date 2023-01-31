# coding: utf-8

from .protocol import Protocol


class UdpProtocol(Protocol):

    def send_dgram(self, data: bytes, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        if not isinstance(data, bytes):
            return

        self.connection.write_dgram(data, addr)

    def dgram_received(self, data: bytes, addr):
        """

        :param data:
        :param addr:
        :return:
        """
