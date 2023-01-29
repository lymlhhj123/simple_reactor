# coding: utf-8

from .tcp_connector import TcpConnector
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, event_loop, ctx, timeout=10, auto_reconnect=False, is_ipv6=False):
        """

        :param host:
        :param port:
        :param event_loop:
        :param ctx:
        :param timeout:
        :param auto_reconnect:
        :param is_ipv6:
        """
        self.event_loop = event_loop
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect

        self.connector = TcpConnector((host, port), event_loop, ctx, is_ipv6)
        self.connector.set_err_callback(self._on_connection_error)

    def start(self):
        """

        :return:
        """
        self.connector.start_connect(self.timeout)

    def _on_connection_error(self, error):
        """

        :param error:
        :return:
        """
        readable = const.ConnectionErr.MAP[error]
        logger.error(f"connection broken with server, {readable}")

        if self.auto_reconnect:
            self.event_loop.call_later(3, self.connector.start_connect, self.timeout)
