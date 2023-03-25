# coding: utf-8

import socket

from .. import fd_helper
from .. import sock_helper
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

        sock_helper.set_sock_async(sock)

        if self.options.tcp_no_delay:
            sock_helper.set_tcp_no_delay(sock)

        if self.options.tcp_keepalive:
            sock_helper.set_tcp_keepalive(sock)

        fd_helper.close_on_exec(sock.fileno(), self.options.close_on_exec)

        conn = Connection(sock, self.ctx, self.ev)
        conn.try_open(self.endpoint, self.options.connect_timeout)
