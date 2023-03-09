# coding: utf-8

import socket
import random
import ipaddress

from .. import sock_helper
from .tcp_connection import TcpConnection
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, ev, ctx, timeout=10, auto_reconnect=False):

        self.host = host
        self.port = port
        self.ev = ev
        self.ctx = ctx
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect

        address = ipaddress.ip_address(host)
        if address.version == 4:
            self.family = socket.AF_INET
        else:
            self.family = socket.AF_INET6

        self.ev.call_soon(self._try_connect)

    def _try_connect(self):
        """

        :return:
        """
        sock = socket.socket(self.family, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)
        sock_helper.set_tcp_no_delay(sock)
        sock_helper.set_tcp_keepalive(sock)

        conn = TcpConnection(sock, self.ctx, self.ev)
        conn.set_established_callback(self._connection_established)
        conn.set_error_callback(self._connection_error)
        conn.set_failure_callback(self._connection_failed)
        conn.set_closed_callback(self._connection_closed)

        conn.try_open((self.host, self.port), self.timeout)

    def _connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        self.ctx.connection_established(protocol)

    def _connection_error(self, conn):
        """

        :return:
        """
        reason = conn.str_error()
        logger.error(f"error happened with {self.host}:{self.port}, reason: {reason}")

        if self.auto_reconnect:
            self._reconnect()

        self.ctx.connection_error(conn)

    def _connection_failed(self, conn):
        """

        :return:
        """
        reason = conn.str_error()
        logger.error(f"failed to connect {self.host}:{self.port}, reason: {reason}")

        if self.auto_reconnect:
            self._reconnect()

        self.ctx.connection_failure(conn)

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        self.ctx.connection_closed(conn)

    def _reconnect(self):
        """

        :return:
        """
        delay = random.random() * 5
        logger.info(f"reconnect to server after {delay} seconds")
        self.ev.call_later(delay, self._try_connect)
