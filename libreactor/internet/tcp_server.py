# coding: utf-8

import errno
import socket

from .tcp_connection import TcpConnection
from ..channel import Channel
from .. import utils
from .. import const
from libreactor import sock_helper
from libreactor import logging

logger = logging.get_logger()


class TcpServer(object):

    def __init__(self, port, ev, ctx, backlog=1024, ipv6_only=False):

        self.port = port
        self.ev = ev
        self.ctx = ctx
        self.backlog = backlog
        self.ipv6_only = ipv6_only

        self.placeholder = open("/dev/null")

        self.sock = None
        self.channel = None

        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock_helper.set_reuse_addr(self.sock)
        if self.ipv6_only:
            sock_helper.set_ipv6_only(self.sock)

        self.sock.bind((const.IPAny.V6, self.port))
        self.sock.listen(self.backlog)

        self.channel = Channel(self.sock.fileno(), self.ev)
        self.channel.set_read_callback(self._on_read_event)
        self.channel.enable_reading()

    def _on_read_event(self):
        """

        :return:
        """
        while True:
            try:
                sock, addr = self.sock.accept()
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    break
                elif err_code == errno.EMFILE:
                    self._too_many_open_file()
                else:
                    self._accept_error()
                    logger.error("unknown error happened, exit server, %s", e)
                    break
            else:
                self._on_new_connection(sock, addr)

    def _too_many_open_file(self):
        """

        :return:
        """
        logger.error("too many open file, accept and close connection")
        self.placeholder.close()
        sock, _ = self.sock.accept()
        sock.close()
        self._placeholder = open("/dev/null")

    def _accept_error(self):
        """

        :return:
        """
        self.channel.disable_reading()
        self.channel.close()

        del self.channel
        del self.sock

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        logger.info(f"new connection from {addr}, fd: {sock.fileno()}")

        sock_helper.set_tcp_no_delay(sock)
        sock_helper.set_tcp_keepalive(sock)

        conn = TcpConnection(sock, self.ctx, self.ev)
        conn.set_made_callback(self._connection_made)
        conn.set_error_callback(self._connection_error)
        conn.set_closed_callback(self._connection_closed)

        self.ev.call_soon(conn.connection_made, addr)

    def _connection_made(self, protocol):
        """

        :param protocol:
        :return:
        """
        self.ctx.connection_made(protocol)

    def _connection_error(self, conn):
        """

        :return:
        """
        self.ctx.connection_error(conn)

    def _connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        self.ctx.connection_closed(conn)
