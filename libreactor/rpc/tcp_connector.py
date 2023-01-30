# coding: utf-8

import socket

from .tcp_connection import TcpConnection
from libreactor import sock_util
from libreactor.dns_resolver import DNSResolver
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpConnector(object):

    def __init__(self, host, port, event_loop, ctx, timeout=10):
        """

        :param host:
        :param port:
        :param event_loop:
        :param ctx:
        :param timeout:
        """
        self.host = host
        self.port = port
        self.event_loop = event_loop
        self.ctx = ctx
        self.timeout = timeout

        self._err_callback = None

    def set_err_callback(self, err_callback):
        """

        :param err_callback:
        :return:
        """
        self._err_callback = err_callback

    def start_connect(self):
        """

        :return:
        """
        resolver = DNSResolver(self.host, self.port, self.event_loop)
        resolver.set_callback(on_result=self._dns_result)
        resolver.start()

    def _dns_result(self, status, addr_list):
        """

        :param status:
        :param addr_list:
        :return:
        """
        assert self.event_loop.is_in_loop_thread()

        if status == const.DNSResolvStatus.OK:
            af, _, _, _, sa = addr_list[0]
            self._connect_in_loop(af, sa, self.timeout)
        else:
            self._connection_error(const.ConnectionErr.DNS_FAILED)

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
