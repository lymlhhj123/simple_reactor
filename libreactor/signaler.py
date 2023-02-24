# coding: utf-8

from . import fd_helper


class Signaler(object):

    def __init__(self):

        self.r_fd, self.w_fd = fd_helper.make_async_pipe()

    def fileno(self):
        """

        :return:
        """
        return self.r_fd

    def read_all(self):
        """

        :return:
        """
        fd_helper.read_fd_all(self.r_fd)

    def read_one(self):
        """
        read one byte
        :return:
        """
        fd_helper.read_fd(self.r_fd, 1)

    def write_one(self):
        """
        write one byte
        :return:
        """
        fd_helper.write_fd(self.w_fd, b"1")

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        assert isinstance(data, bytes)
        fd_helper.write_fd(self.w_fd, data)
