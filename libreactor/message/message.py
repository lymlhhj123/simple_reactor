# coding: utf-8

import zlib
import json
from typing import Union

from .header import Header


class Message(object):

    CHARSET = "utf-8"
    VER = 1

    def __init__(self, header, data: bytes):

        self.header = header

        self.data = data

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

        return cls(header, data)

    def as_bytes(self):
        """

        :return:
        """
        return self.header.as_bytes() + self.data

    def raw(self):
        """
        return raw bytes
        :return:
        """
        return self.data

    def text(self):
        """
        return unicode str
        :return:
        """
        return self.data.decode(self.CHARSET)

    def json(self):
        """

        :return:
        """
        return json.loads(self.text())

    def is_broken(self):
        """

        :return:
        """
        if zlib.crc32(self.data) != self.header.crc32:
            return True

        return False
