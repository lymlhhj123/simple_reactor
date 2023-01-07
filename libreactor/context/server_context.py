# coding: utf-8

from .context import Context
from .. import rpc


class ServerContext(Context):

    def __init__(self):

        super(ServerContext, self).__init__()
        self.acceptor = None

    def listen_tcp(self, port, event_loop, backlog=8):
        """

        :param port:
        :param event_loop:
        :param backlog:
        :return:
        """
        self.acceptor = rpc.TcpAcceptor(port, self, event_loop, backlog)
        self.acceptor.start_accept()

    def on_accept_error(self, ex):
        """

        :param ex:
        :return:
        """
        self.logger().error(f"error happened on listen sock, {ex}")
        self.acceptor.start_accept()
