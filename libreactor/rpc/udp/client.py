# coding: utf-8

import os
import socket

from .connection import Connection
from libreactor.utils import errno_from_ex


class Client(object):

    def __init__(self, endpoint, context):
        """

        :param endpoint:
        :param context:
        """
        self._endpoint = endpoint
        self._context = context

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
        try:
            addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_DGRAM)
        except Exception as e:
            err_code = errno_from_ex(e)
            self._context.logger().error(f"failed to dns resolve {self._endpoint}, {os.strerror(err_code)}")
            return

        if not addr_list:
            self._context.logger().error(f"dns resolve {self._endpoint} is empty")
            return

        for af, _, _, _, _ in addr_list:
            s = socket.socket(af, socket.SOCK_DGRAM)
            conn = Connection(s, self._event_loop, self._context)
            conn.set_on_connection_established(self._connection_established)

            self._event_loop.call_soon(conn.connection_established)
