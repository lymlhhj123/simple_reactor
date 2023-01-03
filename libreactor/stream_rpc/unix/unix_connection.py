# coding: utf-8

import socket

from ..connection import Connection


class UnixConnection(Connection):

    @classmethod
    def try_open(cls, sa, context, event_loop, timeout=10):
        """

        :param sa:
        :param context:
        :param event_loop:
        :param timeout:
        :return:
        """
        sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM)
        conn = cls._try_open(sock, sa, context, event_loop, timeout=10)
        if not conn:
            sock.close()
            del sock
        else:
            return conn
