# coding: utf-8

import zlib
from typing import Union

from .header import Header
from .message import Message
from .bytes_buffer import BytesBuffer


class MessageFactory(object):

    def __init__(self):

        self.message = Message()

    def from_str(self, data: Union[bytes, str]):
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

    def from_buffer(self, buffer_: BytesBuffer):
        """

        :return:
        """
        retrieved = self._retrieve_header(buffer_)
        if retrieved == -1:
            return

        msg_len = self.message.header.msg_len
        if buffer_.size() < msg_len:
            return

        data = buffer_.retrieve(msg_len)
        self.message.set_data(data)

        msg, self.message = self.message, Message()
        assert msg.is_completed()
        return msg

    def _retrieve_header(self, buffer_: BytesBuffer):
        """

        :return:
        """
        if self.message.header:
            return 0

        header_len = Header.HEADER_LEN
        if buffer_.size() < header_len:
            return -1

        header_bytes = buffer_.retrieve(header_len)
        header = Header.from_bytes(header_bytes)
        self.message.header = header
        return 0
