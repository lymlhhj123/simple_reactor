# coding: utf-8

import socket

from .tcp_connection import TcpConnection
from libreactor import sock_util
from libreactor import logging

logger = logging.get_logger()


class TcpConnector(object):

    def __init__(self, family, endpoint, event_loop, ctx, timeout=10):
        """

        :param family:
        :param endpoint:
        :param event_loop:
        :param ctx:
        :param timeout:
        """
        self.family = family
        self.endpoint = endpoint
        self.event_loop = event_loop
        self.ctx = ctx
        self.timeout = timeout

        self.closed_callback = None

    def set_closed_callback(self, closed_callback):
        """

        :param closed_callback:
        :return:
        """
        self.closed_callback = closed_callback

    def start_connect(self):
        """

        :return:
        """
        assert self.event_loop.is_in_loop_thread()

        self._connect_in_loop(self.family, self.endpoint, self.timeout)

    def _connect_in_loop(self, family, endpoint, timeout):
        """

        :param family:
        :param endpoint:
        :param timeout:
        :return:
        """
        sock = socket.socket(family=family, type=socket.SOCK_STREAM)
        sock_util.set_tcp_no_delay(sock)
        sock_util.set_tcp_keepalive(sock)

        conn = TcpConnection(sock, self.ctx, self.event_loop)
        conn.set_closed_callback(closed_callback=self._connection_closed)
        conn.try_open(endpoint, timeout)

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        if self.closed_callback:
            self.closed_callback(conn)
