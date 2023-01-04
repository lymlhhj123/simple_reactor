# coding: utf-8

from .protocol import Protocol


class Dgram(Protocol):

    def safe_send_dgram(self, data, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
        self.event_loop.call_soon(self.send_dgram, data, addr)

    def send_dgram(self, data, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
        self.connection.write_dgram(data, addr)

    def dgram_received(self, data, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
