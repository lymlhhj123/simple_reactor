# coding: utf-8

from .connector import Connector
from .. import sock_helper
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, ev, ctx, timeout=10):

        self.host = host
        self.port = port
        self.ev = ev

        ctx.bind_client(self)
        self.ctx = ctx
        self.timeout = timeout

    def connect(self):
        """

        :return:
        """
        self.ev.call_soon(self._try_connect)

    def _try_connect(self):
        """

        :return:
        """
        family = sock_helper.get_family_by_ip(self.host)
        connector = Connector(family, (self.host, self.port), self.ctx, self.ev)
        connector.connect(self.timeout)

    def endpoint(self):
        """

        :return:
        """
        return self.host, self.port
