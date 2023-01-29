# coding: utf-8

import socket

from .tcp_connection import TcpConnection
from libreactor import sock_util
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpConnector(object):

    def __init__(self, endpoint, event_loop, ctx, is_ipv6):
        """

        :param endpoint:
        :param event_loop:
        :param ctx:
        :param is_ipv6:
        """
        self.ctx = ctx
        self.event_loop = event_loop
        self.endpoint = endpoint
        self.is_ipv6 = is_ipv6

        self._err_callback = None

    def set_err_callback(self, err_callback):
        """

        :param err_callback:
        :return:
        """
        self._err_callback = err_callback

    def start_connect(self, timeout=10):
        """

        :param timeout:
        :return:
        """
        host, port = self.endpoint
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        try:
            addr_list = socket.getaddrinfo(host, port, family, socket.SOCK_STREAM)
        except Exception as ex:
            logger.error(f"failed to dns resolve {host}, {ex}")
            return

        if not addr_list:
            logger.warn("dns resolve is empty")
            return

        af, _, _, _, sa = addr_list[0]
        self.event_loop.call_soon(self._connect_in_loop, af, sa, timeout)

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
        conn.set_callback(err_callback=self._connection_error)
        conn.try_open(timeout)

    def _connection_error(self, error: const.ConnectionErr):
        """

        :param error:
        :return:
        """
        if self._err_callback:
            self._err_callback(error)
