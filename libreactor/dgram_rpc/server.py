# coding: utf-8

import socket

from .connection import Connection


class Server(object):

    def __init__(self, endpoint, context):
        """

        :param endpoint:
        :param context:
        """
        self._endpoint = endpoint
        self._context = context

        self._event_loop = context.get_event_loop()

    def start(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.bind(("::", self._endpoint))

        conn = Connection.open(s, self._event_loop, self._context)
        self._event_loop.call_soon(conn.connection_made)
