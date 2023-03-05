# coding: utf-8

import zlib
import json
from typing import Union

from .header import Header


class Message(object):

    Encoding = "utf-8"

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
            data = data.encode(cls.Encoding)

        crc32 = zlib.crc32(data)
        msg_len = len(data)
        ext_len = len(header_extension)
        header = Header(crc32, msg_len, ext_len)
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

    def text(self, encoding=None):
        """
        return unicode str
        :return:
        """
        encoding = encoding if encoding else self.Encoding
        return self.data.decode(encoding)

    def json(self, encoding=None):
        """

        :return:
        """
        return json.loads(self.text(encoding))

    def is_broken(self):
        """

        :return:
        """
        if zlib.crc32(self.data) != self.header.crc32:
            return True

        return False
