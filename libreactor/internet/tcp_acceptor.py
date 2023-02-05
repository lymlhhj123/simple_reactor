# coding: utf-8

import os
import errno
import socket

from libreactor.channel import Channel
from libreactor.utils import errno_from_ex
from libreactor import sock_util
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpAcceptor(object):

    def __init__(self, port, event_loop, backlog=8, is_ipv6=False):
        """

        :param port:
        :param event_loop:
        :param backlog:
        :param is_ipv6:
        """
        self.port = port
        self.ev = event_loop
        self.backlog = backlog
        self.is_ipv6 = is_ipv6

        self.placeholder = open("/dev/null")

        self.sock = None
        self.channel = None
        self.new_connection_callback = None

        self._create_sock_channel()

    def _create_sock_channel(self):
        """

        :return:
        """
        if self.is_ipv6:
            family, addr_any = socket.AF_INET6, const.IPAny.v6
        else:
            family, addr_any = socket.AF_INET, const.IPAny.V4

        sock = socket.socket(family, socket.SOCK_STREAM)
        sock_util.set_tcp_reuse_addr(sock)
        sock.bind((addr_any, self.port))
        sock.listen(self.backlog)
        self.sock = sock

        self.channel = Channel(sock.fileno(), self.ev)
        self.channel.set_read_callback(self._on_read_event)

    def set_new_connection_callback(self, new_connection_callback):
        """

        :param new_connection_callback:
        :return:
        """
        self.new_connection_callback = new_connection_callback

    def start_accept(self):
        """

        :return:
        """
        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        self.channel.enable_reading()

    def _on_read_event(self):
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
                    self._accept_error(err_code)
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
        if self.new_connection_callback:
            self.new_connection_callback(sock, addr)
        else:
            sock.close()

    def _accept_error(self, err_code):
        """

        :param err_code:
        :return:
        """
        logger.error(f"error happened on accept: {os.strerror(err_code)}")
        self.channel.close()
        self.channel = None
        self.sock = None

        self._create_sock_channel()
        self._start_in_loop()