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
        self.endpoint = host, port
        self.event_loop = event_loop
        self.auto_reconnect = auto_reconnect

        self.connector = TcpConnector(host, port, event_loop, ctx, timeout)
        self.connector.set_callback(on_error=self._on_error)

    def start(self):
        """

        :return:
        """
        self.event_loop.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        self.connector.start_connect()

    def _on_error(self, error):
        """

        :param error:
        :return:
        """
        readable = const.ConnectionErr.MAP[error]
        logger.error(f"connection broken with server: {self.endpoint}, err: {readable}")
        self._reconnect()

    def _reconnect(self):
        """

        :return:
        """
        if not self.auto_reconnect:
            return

        delay = random.random() * 5
        logger.info(f"reconnect to server after {delay} seconds")
        self.event_loop.call_later(delay, self.connector.start_connect)
