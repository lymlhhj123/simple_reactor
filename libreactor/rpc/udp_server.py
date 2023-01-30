# coding: utf-8

import socket

from .udp_connection import UdpConnection


class UdpServer(object):

    def __init__(self, endpoint, event_loop, ctx):
        """

        :param endpoint:
        :param event_loop:
        :param ctx:
        """
        self._endpoint = endpoint
        self._event_loop = event_loop
        self._ctx = ctx

    def start_accept(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.bind(("::", self._endpoint))

        conn = UdpConnection(s, self._event_loop, self._ctx)
        self._event_loop.call_soon(conn.connection_made)
