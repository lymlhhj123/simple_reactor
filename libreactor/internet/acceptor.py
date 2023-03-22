# coding: utf-8

import errno
import socket

from connection import Connection
from ..channel import Channel
from .. import sock_helper
from .. import utils
from .. import logging

logger = logging.get_logger()


class Acceptor(object):

    def __init__(self, family, endpoint, ctx, ev, backlog=128, ipv6_only=False):
        """

        :param family:
        :param endpoint:
        :param ctx:
        :param ev:
        :param backlog:
        :param ipv6_only:
        """
        self.family = family
        self.endpoint = endpoint
        self.ctx = ctx
        self.ev = ev
        self.backlog = backlog
        self.ipv6_only = ipv6_only

        self.placeholder = open("/dev/null")

        self.sock = None
        self.channel = None

    def start(self):
        """

        :return:
        """
        assert self.ev.is_in_loop_thread()

        self.sock = sock = socket.socket(self.family, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)
        sock_helper.set_reuse_addr(sock)

        if self.family == socket.AF_INET6 and self.ipv6_only:
            sock_helper.set_ipv6_only(sock)

        sock.bind(self.endpoint)
        sock.listen(self.backlog)

        self.channel = Channel(sock.fileno(), self.ev)
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

        self.ev.call_soon(self.start)

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

        conn = Connection(sock, self.ctx, self.ev)
        self.ev.call_soon(conn.connection_made, addr)
