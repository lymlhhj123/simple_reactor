# coding: utf-8

import socket

from ..acceptor import Acceptor
from libreactor import sock_util
from libreactor import fd_util


class TcpAcceptor(Acceptor):

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
