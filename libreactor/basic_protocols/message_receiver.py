# coding: utf-8

from typing import Union

from ..models import Message
from ..protocol import Protocol
from ..message_factory import MessageFactory
from .. import logging

logger = logging.get_logger()


class MessageReceiver(Protocol):

    def __init__(self):

        super(MessageReceiver, self).__init__()

        self.buffer = b""
        self.msg_factory = MessageFactory()

    def send_data(self, data: Union[bytes, str]):
        """

        :param data:
        :return:
        """
        msg = self.msg_factory.create(data)
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
        self.buffer += data
        while True:
            try:
                read_size = self.msg_factory.from_stream(self.buffer)
            except Exception as ex:
                logger.error(f"header broken: {ex}")
                self.msg_broken()
                return

            if read_size == -1:
                return

            self.buffer = self.buffer[read_size:]

            msg = self.msg_factory.retrieve()
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
