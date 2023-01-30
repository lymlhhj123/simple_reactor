# coding: utf-8

import random

from .tcp_connector import TcpConnector
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, event_loop, ctx, timeout=10, auto_reconnect=False):
        """

        :param host:
        :param port:
        :param event_loop:
        :param ctx:
        :param timeout:
        :param auto_reconnect:
        """
        self.event_loop = event_loop
        self.auto_reconnect = auto_reconnect

        self.endpoint = host, port

        self.connector = TcpConnector(host, port, event_loop, ctx, timeout)
        self.connector.set_err_callback(self._on_connection_error)

    def start(self):
        """

        :return:
        """
        self.connector.start_connect()

    def _on_connection_error(self, error):
        """

        :param error:
        :return:
        """
        readable = const.ConnectionErr.MAP[error]
        logger.error(f"connection broken with server: {self.endpoint}, err: {readable}")

        if self.auto_reconnect:
            delay = random.random() * 3
            logger.info(f"reconnect to server after {delay} seconds")
            self.event_loop.call_later(delay, self.connector.start_connect)
