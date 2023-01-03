# coding: utf-8

import socket

from .connection import Connection


class Client(object):

    def __init__(self, endpoint, context, family=socket.AF_INET):
        """

        :param endpoint: unused args
        :param context:
        :param family:
        """
        self._endpoint = endpoint
        self._context = context
        self._family = family

        self._event_loop = context.get_event_loop()

        self._on_connection_established = None

    def set_on_connection_established(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_established = callback

    def _connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        if self._on_connection_established:
            self._on_connection_established(protocol)

    def start(self):
        """

        :return:
        """
        host, port = self._endpoint
        addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_DGRAM)
        for af, _, _, _, _ in addr_list:
            s = socket.socket(af, socket.SOCK_DGRAM)
            conn = Connection.open(s, self._event_loop, self._context)
            conn.set_on_connection_established(self._connection_established)

            self._event_loop.call_soon(conn.connection_established)
            return

        self._context.logger().error(f"failed to parse {self._endpoint}")
