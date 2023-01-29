# coding: utf-8

from .tcp_acceptor import TcpAcceptor
from .tcp_connection import TcpConnection
from libreactor import sock_util
from libreactor import logging

logger = logging.get_logger()


class TcpServer(object):

    def __init__(self, port, event_loop, ctx, backlog=8):
        """

        :param port:
        :param event_loop:
        :param ctx:
        :param backlog:
        """
        self.ctx = ctx
        self.event_loop = event_loop

        self.acceptor = TcpAcceptor(port, event_loop, backlog)
        self.acceptor.set_new_connection_callback(self._on_new_connection)

        self._connection_set = set()

    def start(self):
        """

        :return:
        """
        self.acceptor.start_accept()

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """

        assert self.event_loop.is_in_loop_thread()

        logger.info(f"new connection from {addr}, fd: {sock.fileno()}")

        sock_util.set_tcp_no_delay(sock)
        sock_util.set_tcp_keepalive(sock)

        conn = TcpConnection.from_sock(sock, self.ctx, self.event_loop)
        self._connection_set.add(conn)
        conn.set_callback(closed_callback=self._connection_closed)
        conn.connection_made()

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        logger.info(f"server side connection closed. fileno: {conn.fileno()}")
        self._connection_set.remove(conn)
