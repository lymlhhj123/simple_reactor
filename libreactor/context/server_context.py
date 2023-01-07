# coding: utf-8

from .context import Context
from .. import rpc


class ServerContext(Context):

    def __init__(self):

        super(ServerContext, self).__init__()
        self.acceptor = None

    def listen_tcp(self, port, event_loop):
        """

        :param port:
        :param event_loop:
        :return:
        """
        self.acceptor = rpc.TcpAcceptor(port, self, event_loop)
        self.acceptor.start_accept()

    def on_connection_made(self, protocol):
        """

        :param protocol:
        :return:
        """

    def on_accept_error(self, ex):
        """

        :param ex:
        :return:
        """
        self.logger().error(f"error happened on listen sock, {ex}")
        self.acceptor.start_accept()
