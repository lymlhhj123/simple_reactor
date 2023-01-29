# coding: utf-8

import errno
import socket

from libreactor.io_stream import IOStream
from libreactor.utils import errno_from_ex
from libreactor import fd_util
from libreactor import sock_util
from libreactor import logging

logger = logging.get_logger()


class TcpAcceptor(IOStream):

    def __init__(self, port, event_loop, backlog=8):
        """

        :param port:
        :param event_loop:
        :param backlog:
        """
        self.port = port
        self.backlog = backlog
        self.placeholder = open("/dev/null")

        self.sock = self._create_listen_sock()

        fd_util.make_fd_async(self.sock.fileno())
        fd_util.close_on_exec(self.sock.fileno())

        super(TcpAcceptor, self).__init__(self.sock.fileno(), event_loop)

        self._new_connection_callback = None

    def _create_listen_sock(self):
        """

        :return:
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock_util.set_tcp_reuse_addr(s)
        s.bind(("::", self.port))
        s.listen(self.backlog)
        return s

    def set_new_connection_callback(self, new_connection_callback=None):
        """

        :param new_connection_callback:
        :return:
        """
        self._new_connection_callback = new_connection_callback

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
                sock, addr = self.sock.accept()
            except socket.error as e:
                err_code = errno_from_ex(e)
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    break
                elif err_code == errno.EMFILE:
                    self._too_many_open_file()
                else:
                    self.close()
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

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        if self._new_connection_callback:
            self._new_connection_callback(sock, addr)
        else:
            sock.close()
