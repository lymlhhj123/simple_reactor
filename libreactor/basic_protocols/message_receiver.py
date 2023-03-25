# coding: utf-8

import json
from typing import Union

from ..message import Message
from ..message import Header
from ..bytes_buffer import BytesBuffer
from ..protocol import Protocol
from .. import logging

logger = logging.get_logger()


class MessageReceiver(Protocol):

    def __init__(self):

        super(MessageReceiver, self).__init__()

        self.buffer = BytesBuffer()

        self.header = None
        self.header_len = Header.HEADER_LEN
        self.ext_len = 0
        self.msg_len = 0

    def send_json(self, data):
        """

        :param data:
        :return:
        """
        self.send_data(json.dumps(data))

    def send_data(self, data: Union[bytes, str]):
        """

        :param data:
        :return:
        """
        msg = Message.create(data)
        self.send_msg(msg)

    def send_msg(self, msg):
        """

        :param msg:
        :return:
        """
        if not isinstance(msg, Message):
            logger.error(f"must be {type(Message)}, not {type(msg)}")
            return

        self.connection.write(msg.as_bytes())

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.buffer.extend(data)
        while True:
            if self._retrieve_header() is False:
                break

            # assert self.header is not None

            if self._retrieve_header_extension() is False:
                break

            assert self.header is not None and self.header.is_completed()

            status, data = self._retrieve_data()
            if status != 0:
                break

            header, self.header = self.header, None
            msg = Message(header, data)
            if msg.is_broken():
                self.msg_broken()
                break

            self.msg_received(msg)
            self.buffer.trim()

    def _retrieve_header(self):
        """

        :return:
        """
        if self.header:
            return True

        if self.buffer.size() < self.header_len:
            return False

        header = Header.from_buffer(self.buffer)
        self.ext_len = header.ext_len()
        self.msg_len = header.msg_len()
        self.header = header
        return True

    def _retrieve_header_extension(self):
        """

        :return:
        """
        if self.ext_len == 0:
            return True

        if self.buffer.size() < self.ext_len:
            return False

        extension = self.buffer.retrieve(self.ext_len)
        self.header.set_extension(extension)
        return True

    def _retrieve_data(self):
        """

        :return:
        """
        if self.msg_len == 0:
            return 0, b""

        if self.buffer.size() < self.msg_len:
            return -1, b""

        data = self.buffer.retrieve(self.msg_len)
        return 0, data

    def msg_broken(self):
        """

        :return:
        """
        self.close_connection()

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
