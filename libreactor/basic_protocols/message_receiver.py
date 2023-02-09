# coding: utf-8

from libreactor import TcpProtocol
from libreactor.message import Message, Header
from libreactor import logging

logger = logging.get_logger()


class MessageReceiver(TcpProtocol):

    def __init__(self):

        super(MessageReceiver, self).__init__()

        self._buffer = b""
        self._header = None

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
        self._buffer += data
        while True:
            if self._header is None:
                if self._retrieve_header() is False:
                    return

            assert self._header is not None
            msg_len = self._header.msg_len
            if len(self._buffer) < msg_len:
                return

            header, self._header = self._header, None
            try:
                data, self._buffer = self._buffer[:msg_len], self._buffer[msg_len:]
                msg = Message.create(data)
                if msg.header != header:
                    self.msg_broken()
                else:
                    self.msg_received(msg)
            except Exception as e:
                logger.error(f"error happened when process msg, {e}")

    def _retrieve_header(self):
        """

        :return:
        """
        header_len = Header.HEADER_LEN
        if len(self._buffer) < header_len:
            return False

        header_bytes, self._buffer = self._buffer[:header_len], self._buffer[header_len:]
        try:
            header = Header.from_bytes(header_bytes)
        except Exception as ex:
            self.header_broken(ex)
            return False

        self._header = header
        return True

    def header_broken(self, ex):
        """

        :param ex:
        :return:
        """
        logger.error(f"header broken: {ex}")
        self.close_connection()

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
