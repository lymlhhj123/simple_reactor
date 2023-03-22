# coding: utf-8

import socket

from .. import sock_helper
from .connection import Connection


class Connector(object):

    def __init__(self, family, endpoint, ctx, ev):
        """

        :param family:
        :param endpoint:
        :param ctx:
        :param ev:
        """
        self.family = family
        self.endpoint = endpoint
        self.ctx = ctx
        self.ev = ev

    def connect(self, timeout=10):
        """

        :param timeout:
        :return:
        """
        sock = socket.socket(self.family, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)
        sock_helper.set_tcp_no_delay(sock)
        sock_helper.set_tcp_keepalive(sock)

        conn = Connection(sock, self.ctx, self.ev)
        conn.try_open(self.endpoint, timeout)
