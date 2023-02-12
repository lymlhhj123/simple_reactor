# coding: utf-8

from typing import Union

from ..models import BytesBuffer
from ..models import Message
from ..models import MessageFactory
from ..protocol import Protocol
from .. import logging

logger = logging.get_logger()


class MessageReceiver(Protocol):

    def __init__(self):

        super(MessageReceiver, self).__init__()

        self.buffer = BytesBuffer()
        self.msg_factory = MessageFactory()

    def send_data(self, data: Union[bytes, str]):
        """

        :param data:
        :return:
        """
        msg = self.msg_factory.from_str(data)
        self.send_msg(msg)

    def send_msg(self, msg: Message):
        """

        :param msg:
        :return:
        """
        if not isinstance(msg, Message):
            logger.error(f"must be Message, not {type(msg)}")
            return

        self.connection.write(msg.as_bytes())

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.buffer.add(data)
        while True:
            try:
                msg = self.msg_factory.from_buffer(self.buffer)
            except Exception as ex:
                logger.error(f"header broken: {ex}")
                self.msg_broken()
                return

            if not msg:
                return

            if msg.is_broken():
                self.msg_broken()
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
