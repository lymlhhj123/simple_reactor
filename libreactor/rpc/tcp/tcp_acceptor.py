# coding: utf-8

import socket

from libreactor.rpc.acceptor import Acceptor
from libreactor import sock_util
from libreactor import fd_util


class TcpAcceptor(Acceptor):

    def __init__(self, context, event_loop, endpoint, backlog=8):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :param backlog:
        """
        super(TcpAcceptor, self).__init__(context, event_loop, endpoint, backlog)

    def _create_listen_sock(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        fd_util.make_fd_async(s.fileno())
        fd_util.close_on_exec(s.fileno())
        sock_util.set_tcp_reuse_addr(s)
        s.bind(("::", self._endpoint))
        s.listen(self._backlog)
        return s
