# coding: utf-8

import os

from .. import common


class Signaler(object):

    def __init__(self, r_fd=None, w_fd=None):
        """

        :param r_fd:
        :param w_fd:
        """
        if not r_fd or not w_fd:
            self.r_fd, self.w_fd = common.make_async_pipe()
        else:
            common.make_fd_async(r_fd)
            common.make_fd_async(w_fd)

            common.close_on_exec(r_fd)
            common.close_on_exec(w_fd)

            self.r_fd = r_fd
            self.w_fd = w_fd

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
            if self._read(4096) == -1:
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
            return -1

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
