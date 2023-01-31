# coding: utf-8

import socket

from .udp_connection import UdpConnection


class UdpServer(object):

    def __init__(self, port, event_loop, ctx):
        """

        :param port:
        :param event_loop:
        :param ctx:
        """
        self.port = port
        self.event_loop = event_loop
        self.ctx = ctx

    def start(self):
        """

        :return:
        """
        conn = self._create_connection()
        self.event_loop.call_soon(conn.connection_made)

    def _create_connection(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.bind(("::", self.port))

        conn = UdpConnection(s, self.event_loop, self.ctx)
        return conn
