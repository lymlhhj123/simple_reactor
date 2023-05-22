# coding: utf-8

from .acceptor import Acceptor
from ..common import const
from ..common import sock_helper


class TcpServer(object):

    def __init__(self, port, ev, ctx, options, host=const.IPAny.V6):
        """

        :param port:
        :param ev:
        :param ctx:
        :param options:
        :param host:
        """
        self.port = port
        self.host = host
        self.ev = ev

        ctx.bind_server(self)
        self.ctx = ctx

        self.options = options

    def start(self):
        """start tcp server

        """
        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        family = sock_helper.get_family_by_ip(self.host)
        endpoint = (self.host, self.port)
        acceptor = Acceptor(family, endpoint, self.ctx, self.ev, self.options)
        acceptor.start()