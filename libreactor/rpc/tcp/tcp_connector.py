# coding: utf-8

from ..connector import Connector
from .tcp_connection import TcpConnection


class TcpConnector(Connector):

    def _make_connection(self, endpoint, context, event_loop, timeout):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :param timeout:
        :return:
        """
        return TcpConnection.try_open(endpoint, context, event_loop, timeout)
