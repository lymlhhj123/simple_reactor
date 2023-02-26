# coding: utf-8

from . import fd_helper


class Signaler(object):

    def __init__(self, r_fd=None, w_fd=None):
        """

        :param r_fd:
        :param w_fd:
        """
        if not r_fd or not w_fd:
            self.r_fd, self.w_fd = fd_helper.make_async_pipe()
        else:
            fd_helper.make_fd_async(r_fd)
            fd_helper.make_fd_async(w_fd)

            fd_helper.close_on_exec(r_fd)
            fd_helper.close_on_exec(w_fd)

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
        fd_helper.read_fd(self.r_fd)

    def read_one(self):
        """
        read one byte
        :return:
        """
        fd_helper.read_once(self.r_fd, 1)

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
