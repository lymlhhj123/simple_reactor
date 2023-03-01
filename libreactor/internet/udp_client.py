# coding: utf-8

import socket
import ipaddress

from .udp_connection import UdpConnection


class UdpClient(object):

    def __init__(self, host, port, ctx, ev):

        self.host = host
        self.port = port
        self.ctx = ctx
        self.ev = ev

        address = ipaddress.ip_address(host)
        if isinstance(address, ipaddress.IPv4Address):
            self.family = socket.AF_INET
        else:
            self.family = socket.AF_INET6

        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        sock = socket.socket(self.family, socket.SOCK_DGRAM)
        conn = UdpConnection(sock, self.ctx, self.ev)
        conn.connection_established((self.host, self.port))
