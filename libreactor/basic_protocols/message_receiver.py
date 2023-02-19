# coding: utf-8

import json
from typing import Union

from ..message import Message
from ..bytes_buffer import BytesBuffer
from ..protocol import Protocol
from .. import logging

logger = logging.get_logger()


class MessageReceiver(Protocol):

    def __init__(self):

        super(MessageReceiver, self).__init__()

        self.buffer = BytesBuffer()
        self.msg = Message()

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
            try:
                if self.msg.create_from_buffer(self.buffer) != 0:
                    return
            except Exception as ex:
                logger.exception(f"msg broken: {ex}")
                self.msg_broken()
                return

            msg, self.msg = self.msg, Message()

            assert msg.is_completed()

            if msg.is_broken():
                self.msg_broken()
                return
            else:
                self.msg_received(msg)

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
