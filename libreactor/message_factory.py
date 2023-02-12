# coding: utf-8

import zlib
from typing import Union

from .models import Header, Message
from .exceptions import HeaderBroken


class MessageFactory(object):

    def __init__(self):

        self.message = None

    def create(self, data: Union[bytes, str]):
        """

        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode(Message.CHARSET)

        crc32 = zlib.crc32(data)
        msg_len = len(data)

        header = Header(crc32, msg_len)
        msg = Message()
        msg.set_header(header)
        msg.set_data(data)
        return msg

    def from_stream(self, stream: bytes):
        """

        :return:
        """
        read_size = self._retrieve_header(stream)
        if read_size == -1:
            return -1

        msg_len = self.message.header.msg_len
        if len(stream[read_size:]) < msg_len:
            return read_size

        data = stream[read_size: read_size + msg_len]
        self.message.set_data(data)
        return read_size + msg_len

    def _retrieve_header(self, stream):
        """

        :return:
        """
        if self.message:
            return 0

        header_len = Header.HEADER_LEN
        if len(stream) < header_len:
            return -1

        header_bytes = stream[:header_len]
        try:
            header = Header.from_bytes(header_bytes)
        except Exception as ex:
            raise HeaderBroken(ex)

        self.message = Message()
        self.message.set_header(header)
        return header_len

    def retrieve(self):
        """

        :return:
        """
        if not self.message or self.message.is_completed() is False:
            return

        message, self.message = self.message, None
        return message
