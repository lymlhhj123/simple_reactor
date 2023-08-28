# coding: utf-8

import os

from .channel import Channel
from ..common import fd_helper


class Waker(object):

    def __init__(self, ev):
        """

        :param ev:
        """
        self.ev = ev

        self.r_fd, self.w_fd = fd_helper.make_async_pipe()

        self.channel = Channel(self.r_fd, ev)

    def enable_reading(self):
        """

        :return:
        """
        self.channel.set_read_callback(self._read)
        self.channel.enable_reading()

    def _read(self):
        """

        :return:
        """
        try:
            os.read(self.r_fd, 4096)
        except IOError:
            pass

    def wake(self, data: bytes = b"x"):
        """

        :param data:
        :return:
        """
        assert isinstance(data, bytes)
        try:
            os.write(self.w_fd, data)
        except IOError:
            pass
