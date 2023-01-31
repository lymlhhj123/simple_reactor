# coding: utf-8

import socket

from .udp_connection import UdpConnection


class UdpClient(object):

    def __init__(self, event_loop, ctx, is_ipv6=False):
        """

        :param event_loop:
        :param ctx:
        :param is_ipv6:
        """
        self.event_loop = event_loop
        self.ctx = ctx
        self.is_ipv6 = is_ipv6

    def start(self):
        """

        :return:
        """
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        s = socket.socket(family, socket.SOCK_DGRAM)
        conn = UdpConnection(s, self.event_loop, self.ctx)
        self.event_loop.call_soon(conn.connection_established)
