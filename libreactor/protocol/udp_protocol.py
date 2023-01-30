# coding: utf-8

from .protocol import Protocol


class UdpProtocol(Protocol):

    def send_dgram(self, data: bytes, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
        self.connection.write_dgram(data, addr)

    def dgram_received(self, data: bytes, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
