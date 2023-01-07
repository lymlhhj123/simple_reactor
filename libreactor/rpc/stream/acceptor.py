# coding: utf-8

import errno
import socket

from libreactor.io_stream import IOStream
from libreactor.utils import errno_from_ex
from libreactor import fd_util
from libreactor import sock_util
from .connection import Connection


class Acceptor(IOStream):

    def __init__(self, ctx, event_loop, endpoint, backlog=8):
        """

        :param ctx:
        :param event_loop:
        :param endpoint:
        :param backlog:
        """
        self._ctx = ctx
        self._endpoint = endpoint
        self._backlog = backlog
        self._placeholder = open("/dev/null")

        self._sock = self._create_listen_sock()

        fd_util.make_fd_async(self._sock.fileno())
        fd_util.close_on_exec(self._sock.fileno())

        super(Acceptor, self).__init__(self._sock.fileno(), event_loop)

    def _create_listen_sock(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock_util.set_tcp_reuse_addr(s)
        s.bind(("::", self._endpoint))
        s.listen(self._backlog)
        return s

    def start_accept(self):
        """

        :return:
        """
        self._event_loop.call_soon(self._start_accept_in_loop)

    def _start_accept_in_loop(self):
        """

        :return:
        """
        self.enable_reading()

    def on_read(self):
        """

        :return:
        """
        while True:
            try:
                sock, addr = self._sock.accept()
            except socket.error as e:
                err_code = errno_from_ex(e)
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    break
                elif err_code == errno.EMFILE:
                    self._too_many_open_file()
                else:
                    self.close()
                    self._ctx.on_accept_error(err_code)
                    break
            else:
                self._on_new_connection(sock, addr)

    def _too_many_open_file(self):
        """

        :return:
        """
        self._ctx.logger().error(f"too many open file, close socket")
        self._placeholder.close()
        sock, _ = self._sock.accept()
        sock.close()
        self._placeholder = open("/dev/null")

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        self._ctx.logger().info(f"new connection from {addr}, fd: {sock.fileno()}")

        sock_util.set_tcp_no_delay(sock)
        sock_util.set_tcp_keepalive(sock)

        conn = Connection.from_sock(sock, self._ctx, self._event_loop)
        conn.connection_made()
