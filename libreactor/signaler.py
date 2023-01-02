# coding: utf-8

from . import fd_util


class Signaler(object):

    def __init__(self):

        self._reader, self._writer = fd_util.make_async_pipe()

    def fileno(self):
        """

        :return:
        """
        return self._reader.fileno()

    def read_all(self):
        """

        :return:
        """
        while True:
            if not self._read():
                break

    def read_one(self):
        """
        read one byte
        :return:
        """
        self._read(size=1)

    def _read(self, size=4096):
        """

        :param size:
        :return:
        """
        try:
            return self._reader.read(size)
        except IOError:
            return ""

    def write_one(self):
        """
        write one byte
        :return:
        """
        self._write(b"1")

    def _write(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        try:
            self._writer.write(bytes_)
        except IOError:
            pass
