# coding: utf-8

import zlib
import json
import struct


class Header(object):

    HEADER_LEN = 10
    HEADER_FMT = "!HII"

    def __init__(self, version, crc32, msg_len):
        """

        :param version:
        :param crc32:
        :param msg_len:
        """
        self.version = version
        self.crc32 = crc32
        self.msg_len = msg_len

    @classmethod
    def from_bytes(cls, data_bytes: bytes):
        """

        :param data_bytes:
        :return:
        """
        v, crc32, msg_len = struct.unpack(cls.HEADER_FMT, data_bytes)
        header = Header(v, crc32, msg_len)
        return header

    def as_bytes(self):
        """

        :return:
        """
        return struct.pack(self.HEADER_FMT, self.version, self.crc32, self.msg_len)

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        return (self.version == other.version and
                self.crc32 == other.crc32 and
                self.msg_len == other.msg_len)


class Message(object):

    VERSION = 1
    CHARSET = "utf-8"

    def __init__(self, header, body):

        self.header = header
        self.body = body

    @classmethod
    def create(cls, data):
        """

        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode(cls.CHARSET)

        crc32 = zlib.crc32(data)
        msg_len = len(data)

        header = Header(cls.VERSION, crc32, msg_len)
        m = Message(header, data)

        return m

    def as_bytes(self):
        """

        :return:
        """
        return self.header.as_bytes() + self.body

    def text(self):
        """

        :return:
        """
        return self.body

    def context(self):
        """

        :return:
        """
        return self.body.decode(self.CHARSET)

    def json(self):
        """

        :return:
        """
        return json.load(self.context())
