# coding: utf-8

import os

from ..common import fd_helper


class Signaler(object):

    def __init__(self):

        self.r_fd, self.w_fd = fd_helper.make_async_pipe()

    def fileno(self):
        """

        :return:
        """
        return self.r_fd

    def write_fd(self):
        """

        :return:
        """
        return self.w_fd

    def read_all(self):
        """

        :return:
        """
        while True:
            if not self._read(4096):
                break

    def read_one(self):
        """
        read one byte
        :return:
        """
        self._read(1)

    def _read(self, chunk_size):
        """

        :param chunk_size:
        :return:
        """
        try:
            return os.read(self.r_fd, chunk_size)
        except IOError:
            return b""

    def write_one(self):
        """
        write one byte
        :return:
        """
        self.write(b"1")

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        assert isinstance(data, bytes)
        try:
            os.write(self.w_fd, data)
        except IOError:
            pass
