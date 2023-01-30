# coding: utf-8

import os
import socket

from .udp_connection import UdpConnection
from libreactor.utils import errno_from_ex


class UdpConnector(object):

    def __init__(self, endpoint, context):
        """

        :param endpoint:
        :param context:
        """
        self._endpoint = endpoint
        self._context = context
        self._event_loop = context.get_event_loop()

    def start_connect(self):
        """

        :return:
        """
        host, port = self._endpoint
        try:
            addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_DGRAM)
        except Exception as e:
            err_code = errno_from_ex(e)
            # todo
            return

        if not addr_list:
            # todo
            return

        af, _, _, _, _ = addr_list[0]
        s = socket.socket(af, socket.SOCK_DGRAM)
        conn = UdpConnection(s, self._event_loop, self._context)
        self._event_loop.call_soon(conn.connection_established)