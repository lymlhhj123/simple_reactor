# coding: utf-8

import zlib
import json
import struct
from typing import Union

from .bytes_buffer import BytesBuffer


class Header(object):

    CRC32_B = 4
    MSG_B = 4
    EXT_B = 2
    HEADER_LEN = CRC32_B + MSG_B + EXT_B
    HEADER_FMT = "!IIH"  # 4 bytes crc32 + 4 bytes msg len + 2 bytes extension len

    def __init__(self, crc32, msg_len, ext_len):
        """

        :param crc32:
        :param msg_len:
        """
        self.crc32 = crc32
        self.msg_len = msg_len
        self.ext_len = ext_len

        self.extension = b""

    def is_completed(self):
        """

        :return:
        """
        return len(self.extension) == self.ext_len

    def as_bytes(self):
        """

        :return:
        """
        return struct.pack(self.HEADER_FMT, self.crc32, self.msg_len, self.ext_len) + self.extension


class Message(object):

    CHARSET = "utf-8"

    def __init__(self):

        self.header = None
        self.data = b""

    @classmethod
    def create(cls, data: Union[str, bytes], header_extension: bytes = b""):
        """

        :param data:
        :param header_extension:
        :return:
        """
        if not isinstance(header_extension, bytes):
            raise TypeError("header extension must be bytes")

        # 2 bytes, so extension len <= 65535
        if len(header_extension) > 65535:
            raise ValueError("header extension must be <= 65535")

        if isinstance(data, str):
            data = data.encode(cls.CHARSET)

        crc32 = zlib.crc32(data)
        msg_len = len(data)
        ext_pen = len(header_extension)
        header = Header(crc32, msg_len, ext_pen)
        header.extension = header_extension

        msg = Message()
        msg.header = header
        msg.data = data
        return msg

    def retrieve_from_buffer(self, bytes_buffer: BytesBuffer):
        """

        :param bytes_buffer:
        :return:
        """
        if self._retrieve_header(bytes_buffer) == -1:
            return -1

        if self._retrieve_header_extension(bytes_buffer) == -1:
            return -1

        msg_len = self.header.msg_len
        if bytes_buffer.size() < msg_len:
            return -1

        data = bytes_buffer.retrieve(msg_len)
        self.data = data
        return 0

    def _retrieve_header(self, bytes_buffer: BytesBuffer):
        """

        :param bytes_buffer:
        :return:
        """
        if self.header:
            return 0

        if bytes_buffer.size() < Header.HEADER_LEN:
            return -1

        crc32 = bytes_buffer.retrieve_uint32()
        msg_len = bytes_buffer.retrieve_uint32()
        ext_len = bytes_buffer.retrieve_uint16()
        header = Header(crc32, msg_len, ext_len)
        self.header = header
        return 0

    def _retrieve_header_extension(self, bytes_buffer):
        """

        :param bytes_buffer:
        :return:
        """
        ext_len = self.header.ext_len
        if ext_len == 0:
            return 0

        if bytes_buffer.size() >= ext_len:
            self.header.extension = bytes_buffer.retrieve(ext_len)
            return 0

        return -1

    def as_bytes(self):
        """

        :return:
        """
        assert self.is_completed()
        return self.header.as_bytes() + self.data

    def context(self):
        """
        return raw bytes
        :return:
        """
        assert self.is_completed()
        return self.data

    def text(self):
        """
        return unicode str
        :return:
        """
        assert self.is_completed()
        return self.data.decode(self.CHARSET)

    def json(self):
        """

        :return:
        """
        return json.loads(self.text())

    def is_completed(self):
        """

        :return:
        """
        if not self.header:
            return False

        if not self.header.is_completed():
            return False

        if len(self.data) != self.header.msg_len:
            return False

        return True

    def is_broken(self):
        """

        :return:
        """
        assert self.is_completed()
        if zlib.crc32(self.data) != self.header.crc32:
            return True

        return False
