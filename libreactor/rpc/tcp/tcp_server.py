# coding: utf-8

from ..server import Server
from .tcp_acceptor import TcpAcceptor
from libreactor import sock_util


class TcpServer(Server):

    def _make_acceptor(self, context, event_loop, endpoint):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :return:
        """
        return TcpAcceptor(context, event_loop, endpoint)

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        self._context.logger().info(f"new connection from {addr}")

        sock_util.set_tcp_no_delay(sock)
        sock_util.set_tcp_keepalive(sock)
        
        self._default_on_new_connection(sock, addr)
