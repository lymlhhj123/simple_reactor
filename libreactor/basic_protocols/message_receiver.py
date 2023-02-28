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

    def send_msg(self, msg: Message):
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
            self._retrieve_header()
            if not self.header:
                break

            if self.header.is_completed() is False:
                self._retrieve_header()

            if self.header.is_completed() is False:
                break

            status, data = self._retrieve_data()
            if status != 0:
                break

            header, self.header = self.header, None
            msg = Message(header, data)
            if msg.is_broken():
                self.msg_broken()
                return

            self.msg_received(msg)
            self.buffer.trim()

    def _retrieve_header(self):
        """

        :return:
        """
        if self.header:
            return

        if self.buffer.size() < Header.HEADER_LEN:
            return

        self.header = Header.from_buffer(self.buffer)

    def _retrieve_header_extension(self):
        """

        :return:
        """
        if self.buffer.size() < self.header.ext_len:
            return

        extension = self.buffer.retrieve(self.header.ext_len)
        self.header.set_extension(extension)

    def _retrieve_data(self):
        """

        :return:
        """
        if self.buffer.size() < self.header.msg_len:
            return -1, b""

        # maybe data is empty
        data = self.buffer.retrieve(self.header.msg_len)
        return 0, data

    def msg_broken(self):
        """

        :return:
        """
        self.close_connection()

    def msg_received(self, msg: Message):
        """

        :param msg:
        :return:
        """
