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

        self._on_closed = None

    def set_callback(self, on_closed=None):
        """

        :param on_closed:
        :return:
        """
        self._on_closed = on_closed

    def start_connect(self):
        """

        :return:
        """
        assert self.event_loop.is_in_loop_thread()

        self._connect_in_loop(self.family, self.endpoint, self.timeout)

    def _connect_in_loop(self, af, sa, timeout):
        """

        :param af:
        :param sa:
        :param timeout:
        :return:
        """
        sock = socket.socket(family=af, type=socket.SOCK_STREAM)
        sock_util.set_tcp_no_delay(sock)
        sock_util.set_tcp_keepalive(sock)
        conn = TcpConnection(sa, sock, self.ctx, self.event_loop)
        conn.set_callback(closed_callback=self._connection_closed)
        conn.try_open(timeout)

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        if self._on_closed:
            self._on_closed()
