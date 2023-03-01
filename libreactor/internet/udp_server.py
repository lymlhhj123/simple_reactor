# coding: utf-8

import socket

from libreactor import sock_helper
from libreactor import const
from .udp_connection import UdpConnection


class UdpServer(object):

    def __init__(self, port, ctx, ev, ipv6_only=False):

        self.port = port
        self.ctx = ctx
        self.ev = ev
        self.ipv6_only = ipv6_only

        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock_helper.set_reuse_addr(sock)
        if self.ipv6_only:
            sock_helper.set_ipv6_only(sock)

        sock.bind((const.IPAny.V6, self.port))

        conn = UdpConnection(sock, self.ctx, self.ev)
        conn.connection_made((const.IPAny.V6, self.port))
