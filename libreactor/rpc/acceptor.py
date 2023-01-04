# coding: utf-8

import errno
import socket

from ..io_stream import IOStream
from ..utils import errno_from_ex
from .. import fd_util


class Acceptor(IOStream):

    def __init__(self, context, event_loop, endpoint, backlog=8):
        """

        :param context:
        :param event_loop:
        :param endpoint:
        :param backlog:
        """
        self._context = context
        self._endpoint = endpoint
        self._backlog = backlog
        self._placeholder = open("/dev/null")

        # called when accept new connection
        self._on_new_connection = None

        self._sock = self._create_listen_sock()

        fd_util.make_fd_async(self._sock.fileno())
        fd_util.close_on_exec(self._sock.fileno())

        super(Acceptor, self).__init__(self._sock.fileno(), event_loop)

    def _create_listen_sock(self):
        """

        :return:
        """
        raise NotImplementedError

    def set_on_new_connection(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_new_connection = callback

    def start_accept(self):
        """

        :return:
        """
        assert self._event_loop.is_in_loop_thread()
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
                    self._context.logger().error(f"error happened on listen sock, {e}")
            else:
                if self._on_new_connection:
                    self._on_new_connection(sock, addr)
                else:
                    sock.close()

    def _too_many_open_file(self):
        """

        :return:
        """
        self._context.logger().error(f"too many open file, close socket")
        self._placeholder.close()
        sock, _ = self._sock.accept()
        sock.close()
        self._placeholder = open("/dev/null")
