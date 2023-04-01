# coding: utf-8

import socket

from .. import common
from .connection import Connection


class Connector(object):

    def __init__(self, family, endpoint, ctx, ev, options):
        """

        :param family:
        :param endpoint:
        :param ctx:
        :param ev:
        :param options:
        """
        self.family = family
        self.endpoint = endpoint
        self.ctx = ctx
        self.ev = ev
        self.options = options

    def connect(self):
        """

        :return:
        """
        sock = socket.socket(self.family, socket.SOCK_STREAM)

        common.set_sock_async(sock)

        if self.options.tcp_no_delay:
            common.set_tcp_no_delay(sock)

        if self.options.tcp_keepalive:
            common.set_tcp_keepalive(sock)

        common.close_on_exec(sock.fileno(), self.options.close_on_exec)

        conn = Connection(sock, self.ctx, self.ev)
        conn.try_open(self.endpoint, self.options.connect_timeout)
