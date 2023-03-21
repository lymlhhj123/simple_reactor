# coding: utf-8

import socket
import ipaddress

from .. import sock_helper
from .tcp_connection import TcpConnection
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, ev, ctx, timeout=10):

        self.host = host
        self.port = port
        self.ev = ev

        ctx.bind_client(self)
        self.ctx = ctx
        self.timeout = timeout

        address = ipaddress.ip_address(host)
        if address.version == 4:
            self.family = socket.AF_INET
        else:
            self.family = socket.AF_INET6

    def connect(self):
        """

        :return:
        """
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
        conn.set_established_callback(self.ctx.connection_established)
        conn.set_error_callback(self.ctx.connection_error)
        conn.set_failure_callback(self.ctx.connection_failure)
        conn.set_closed_callback(self.ctx.connection_closed)

        conn.try_open((self.host, self.port), self.timeout)

    def endpoint(self):
        """

        :return:
        """
        return self.host, self.port
