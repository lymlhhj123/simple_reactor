# coding: utf-8

import socket

from .udp_connection import UdpConnection


class UdpClient(object):

    def __init__(self, host, port, ctx, ev, is_ipv6=False):
        """

        :param host:
        :param port:
        :param ctx:
        :param ev:
        :param is_ipv6:
        """
        self.host = host
        self.port = port
        self.ctx = ctx
        self.ev = ev
        self.is_ipv6 = is_ipv6

    def start(self):
        """

        :return:
        """
        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_DGRAM)

        conn = UdpConnection(sock, self.ctx, self.ev)
        conn.connection_established((self.host, self.port))
