# coding: utf-8

import socket

from .connection import Connection
from libreactor import sock_util


class Connector(object):

    def __init__(self, endpoint, ctx, event_loop):
        """

        :param endpoint:
        :param ctx:
        :param event_loop:
        """
        self.ctx = ctx
        self.event_loop = event_loop
        self.endpoint = endpoint

    def start_connect(self, timeout=10):
        """

        :param timeout:
        :return:
        """
        host, port = self.endpoint
        self.ctx.logger.info(f"start to dns {self.endpoint}")
        try:
            addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except Exception as e:
            self.ctx.logger().error(f"failed to dns resolve {self.endpoint}, {e}")
            return

        if not addr_list:
            self.ctx.logger().error(f"dns resolve {self.endpoint} is empty")
            return

        self.ctx.logger.info("end to dns resolve")

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
        conn = Connection(sa, sock, self.ctx, self.event_loop)
        conn.start_connect(timeout)
