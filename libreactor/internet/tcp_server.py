# coding: utf-8

from .acceptor import Acceptor
from .. import const
from .. import sock_helper
from .. import logging

logger = logging.get_logger()


class TcpServer(object):

    def __init__(self, port, ev, ctx, host=const.IPAny.V4, backlog=1024, ipv6_only=False):
        """

        :param port:
        :param ev:
        :param ctx:
        :param host:
        :param backlog:
        :param ipv6_only:
        """
        self.port = port
        self.host = host
        self.ev = ev

        ctx.bind_server(self)
        self.ctx = ctx

        self.backlog = backlog
        self.ipv6_only = ipv6_only

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
        acceptor = Acceptor(family, endpoint, self.ctx, self.ev, self.backlog, self.ipv6_only)
        acceptor.start()
