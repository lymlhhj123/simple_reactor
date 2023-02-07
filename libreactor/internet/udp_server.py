# coding: utf-8

import socket

from libreactor import sock_util
from libreactor import const
from .udp_connection import UdpConnection


class UdpServer(object):

    def __init__(self, port, ctx, ev, is_ipv6=False):
        """

        :param port:
        :param ctx:
        :param ev:
        :param is_ipv6:
        """
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
        if self.is_ipv6:
            family = socket.AF_INET6
            ip_any = const.IPAny.v6
        else:
            family = socket.AF_INET
            ip_any = const.IPAny.V4

        sock = socket.socket(family, socket.SOCK_DGRAM)
        sock_util.set_reuse_addr(sock)
        sock.bind((ip_any, self.port))

        conn = UdpConnection(sock, self.ctx, self.ev)
        conn.connection_established((ip_any, self.port))
