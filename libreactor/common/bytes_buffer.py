# coding: utf-8

import struct


class BufferEmpty(Exception):

    pass


class BytesBuffer(object):

    def __init__(self):

        self._buffer = bytearray()
        self.read_pos = 0

    def extend(self, data: bytes):
        """

        :param data:
        :return:
        """
        if not isinstance(data, bytes):
            raise TypeError("only accept bytes")

        self._buffer.extend(data)

    def retrieve_int8(self):
        """

        :return:
        """
        data = self.retrieve(1)
        return struct.unpack("!b", data)[0]

    def retrieve_uint8(self):
        """

        :return:
        """
        data = self.retrieve(1)
        return struct.unpack("!B", data)[0]

    def retrieve_int16(self):
        """

        :return:
        """
        data = self.retrieve(2)
        return struct.unpack("!h", data)[0]

    def retrieve_uint16(self):
        """

        :return:
        """
        data = self.retrieve(2)
        return struct.unpack("!H", data)[0]

    def retrieve_int32(self):
        """

        :return:
        """
        data = self.retrieve(4)
        return struct.unpack("!i", data)[0]

    def retrieve_uint32(self):
        """

        :return:
        """
        data = self.retrieve(4)
        return struct.unpack("!I", data)[0]

    def retrieve_int64(self):
        """

        :return:
        """
        data = self.retrieve(8)
        return struct.unpack("!q", data)[0]

    def retrieve_uint64(self):
        """

        :return:
        """
        data = self.retrieve(8)
        return struct.unpack("!Q", data)[0]

    def retrieve(self, size=-1, strict=True):
        """retrieve data from buffer, if size == -1, retrieve all if it

        :param size:
        :param strict:
        :return:
        """
        if size == -1:
            end = self.read_pos + self.size()
        else:
            assert size > 0
            if size > self.size():
                if strict:
                    raise BufferEmpty(f"buffer readable size < {size}")

                end = self.read_pos + self.size()
            else:
                end = self.read_pos + size

        data = self._buffer[self.read_pos: end]
        self.read_pos = end
        return data

    def size(self):
        """
        readable buffer size
        :return:
        """
        readable_size = len(self._buffer) - self.read_pos
        assert readable_size >= 0
        return readable_size

    def trim(self):
        """
        trim buffer, drop data which has been read
        :return:
        """
        del self._buffer[:self.read_pos]
        self.read_pos = 0
