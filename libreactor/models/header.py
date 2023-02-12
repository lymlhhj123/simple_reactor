# coding: utf-8

import struct


class Header(object):

    HEADER_LEN = 8
    HEADER_FMT = "!II"  # 4 bytes crc32 + 4 bytes msg len

    def __init__(self, crc32, msg_len):
        """

        :param crc32:
        :param msg_len:
        """
        self.crc32 = crc32
        self.msg_len = msg_len

    @classmethod
    def from_bytes(cls, data_bytes: bytes):
        """

        :param data_bytes:
        :return:
        """
        crc32, msg_len = struct.unpack(cls.HEADER_FMT, data_bytes)
        header = Header(crc32, msg_len)
        return header

    def as_bytes(self):
        """

        :return:
        """
        return struct.pack(self.HEADER_FMT, self.crc32, self.msg_len)

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        return self.crc32 == other.crc32 and self.msg_len == other.msg_len
