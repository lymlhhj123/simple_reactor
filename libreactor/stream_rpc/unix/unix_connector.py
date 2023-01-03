# coding: utf-8

from libreactor.rpc.connector import Connector
from .unix_connection import UnixConnection


class UnixConnector(Connector):

    def _make_connection(self, endpoint, context, event_loop, timeout):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :param timeout:
        :return:
        """
        return UnixConnection.try_open(endpoint, context, event_loop, timeout)

