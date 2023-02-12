# coding: utf-8


class BytesBuffer(object):

    def __init__(self):

        self._buffer = b""

    def size(self):
        """

        :return:
        """
        return len(self._buffer)

    def add(self, data: bytes):
        """

        :param data:
        :return:
        """
        self._buffer += data

    def retrieve(self, size=-1):
        """

        :param size:
        :return:
        """
        assert size >= -1

        if size == -1:
            buffer_, self._buffer = self._buffer, b""
        else:
            buffer_, self._buffer = self._buffer[:size], self._buffer[size:]

        return buffer_
