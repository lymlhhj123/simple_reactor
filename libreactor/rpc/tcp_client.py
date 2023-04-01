# coding: utf-8

from .connector import Connector
from .. import common

logger = common.get_logger()


class TcpClient(object):

    def __init__(self, host, port, ev, ctx, options):

        self.host = host
        self.port = port
        self.ev = ev

        ctx.bind_client(self)
        self.ctx = ctx
        self.options = options

    def connect(self, delay=0):
        """

        :param delay: delay sec to connect
        :return:
        """
        if delay > 0:
            self.ev.call_later(delay, self._try_connect)
        else:
            self.ev.call_soon(self._try_connect)

    def _try_connect(self):
        """

        :return:
        """
        family = common.get_family_by_ip(self.host)
        connector = Connector(family, (self.host, self.port), self.ctx, self.ev, self.options)
        connector.connect()

    def endpoint(self):
        """

        :return:
        """
        return self.host, self.port
