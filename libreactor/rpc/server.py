# coding: utf-8

from .connection import Connection
from libreactor import fd_util


class Server(object):

    def __init__(self, endpoint, context):
        """

        :param endpoint:
        :param context:
        """
        self._context = context
        self._event_loop = context.get_event_loop()

        self._acceptor = self._make_acceptor(context, self._event_loop, endpoint)

    def _make_acceptor(self, context, event_loop, endpoint):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :return:
        """
        raise NotImplementedError

    def start(self):
        """

        only call once
        :return:
        """
        self._event_loop.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        self._acceptor.set_on_new_connection(self._on_new_connection)
        self._acceptor.start_accept()

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        raise NotImplementedError

    def _default_on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        fd_util.make_fd_async(sock.fileno())
        fd_util.close_on_exec(sock.fileno())
        conn = Connection.from_sock(sock, self._event_loop, self._context)
        self._event_loop.call_soon(conn.connection_made)
