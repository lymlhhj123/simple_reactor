# coding: utf-8

import errno
import socket

from .tcp_connection import TcpConnection
from ..channel import Channel
from .. import utils
from .. import const
from .. import sock_helper
from .. import logging

logger = logging.get_logger()


class TcpServer(object):

    def __init__(self, port, ev, ctx, backlog=1024, ipv6_only=False):

        self.port = port
        self.ev = ev

        ctx.bind_server(self)
        self.ctx = ctx
        self.backlog = backlog
        self.ipv6_only = ipv6_only

        self.placeholder = open("/dev/null")

        self.sock = None
        self.channel = None

    def start(self):
        """start tcp server

        """
        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        sock_helper.set_sock_async(self.sock)
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
                    self._do_accept_error()
                    logger.error("unknown error happened on do accept: %s", e)
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

    def _do_accept_error(self):
        """

        :return:
        """
        self.channel.disable_reading()
        self.channel.close()

        self.sock = None
        self.channel = None

        self.ev.call_soon(self._start_in_loop)

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        logger.info(f"new connection from {addr}, fd: {sock.fileno()}")

        sock_helper.set_sock_async(sock)
        sock_helper.set_tcp_no_delay(sock)
        sock_helper.set_tcp_keepalive(sock)

        conn = TcpConnection(sock, self.ctx, self.ev)
        conn.set_made_callback(self.ctx.connection_made)
        conn.set_error_callback(self.ctx.connection_error)
        conn.set_closed_callback(self.ctx.connection_closed)

        self.ev.call_soon(conn.connection_made, addr)
