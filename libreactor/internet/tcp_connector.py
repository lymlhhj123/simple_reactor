# coding: utf-8

import socket

from .tcp_connection import TcpConnection
from libreactor import sock_helper
from libreactor import logging

logger = logging.get_logger()


class TcpConnector(object):

    def __init__(self, family, endpoint, ev, ctx, timeout=10):
        """

        :param family:
        :param endpoint:
        :param ev:
        :param ctx:
        :param timeout:
        """
        self.family = family
        self.endpoint = endpoint
        self.ev = ev
        self.ctx = ctx
        self.timeout = timeout

        self.on_closed = None
        self.on_error = None
        self.on_failure = None

    def set_closed_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.on_closed = callback

    def set_error_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.on_error = callback

    def set_failure_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.on_failure = callback

    def start_connect(self):
        """

        :return:
        """
        assert self.ev.is_in_loop_thread()

        self._connect_in_loop(self.family, self.endpoint, self.timeout)

    def _connect_in_loop(self, family, endpoint, timeout):
        """

        :param family:
        :param endpoint:
        :param timeout:
        :return:
        """
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock_helper.set_tcp_no_delay(sock)
        sock_helper.set_tcp_keepalive(sock)

        conn = TcpConnection(sock, self.ctx, self.ev)
        conn.set_closed_callback(self._connection_closed)
        conn.set_error_callback(self._connection_error)
        conn.set_failure_callback(self._connection_failed)
        conn.try_open(endpoint, timeout)

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        if self.on_closed:
            self.on_closed(conn)

    def _connection_error(self, err_code):
        """

        :return:
        """
        if self.on_error:
            self.on_error(err_code)

    def _connection_failed(self, err_code):
        """

        :return:
        """
        if self.on_failure:
            self.on_failure(err_code)
