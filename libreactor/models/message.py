# coding: utf-8

import zlib
import json
from typing import Union

from .header import Header


class Message(object):

    CHARSET = "utf-8"

    def __init__(self):

        self.header = None
        self.body = b""

    def set_header(self, header: Header):
        """

        :param header:
        :return:
        """
        self.header = header

    def set_data(self, data: Union[str, bytes]):
        """

        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode(self.CHARSET)

        self.body += data

    def is_completed(self):
        """

        :return:
        """
        if not self.header:
            return False

        if len(self.body) != self.header.msg_len:
            return False

        return True

    def is_broken(self):
        """

        :return:
        """
        assert self.is_completed()
        if zlib.crc32(self.body) != self.header.crc32:
            return True

        return False

    def as_bytes(self):
        """

        :return:
        """
        return self.header.as_bytes() + self.body

    def context(self):
        """
        return raw bytes
        :return:
        """
        return self.body

    def text(self):
        """
        return unicode str
        :return:
        """
        return self.body.decode(self.CHARSET)

    def json(self):
        """

        :return:
        """
        return json.loads(self.text())
