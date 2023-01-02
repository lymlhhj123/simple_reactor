# coding: utf-8

import socket

from ..connection import Connection
from libreactor import sock_util
from libreactor import fd_util


class TcpConnection(Connection):

    @classmethod
    def try_open(cls, sa, context, event_loop, timeout=10):
        """

        :param sa:
        :param context:
        :param event_loop:
        :param timeout:
        :return:
        """
        host, port = sa
        addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for af, _, _, _, sa in addr_list:
            sock = socket.socket(family=af, type=socket.SOCK_STREAM)
            sock_util.set_tcp_no_delay(sock)
            sock_util.set_tcp_keepalive(sock)
            fd_util.close_on_exec(sock.fileno())
            conn = cls._try_open(sock, sa, context, event_loop, timeout)
            if not conn:
                sock.close()
                del sock
                continue

            return conn
