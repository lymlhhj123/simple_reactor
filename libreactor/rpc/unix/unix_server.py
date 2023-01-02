# coding: utf-8

from libreactor.rpc.server import Server
from libreactor.rpc.unix.unix_acceptor import UnixAcceptor


class UnixServer(Server):

    def _make_acceptor(self, context, event_loop, endpoint):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :return:
        """
        return UnixAcceptor(context, event_loop, endpoint)

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        self._context.logger().info(f"new connection on unix, fd: {sock.fileno()}")

        self._default_on_new_connection(sock, addr)
