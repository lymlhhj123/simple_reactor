# coding: utf-8

import socket

from libreactor import logging

logger = logging.get_logger()


class DNSResolver(object):

    def __init__(self, host, port, family, ev):
        """

        :param host:
        :param port:
        :param family:
        :param ev:
        """
        self.host = host
        self.port = port
        self.ev = ev
        self.family = family

        self.on_done = None

    def set_done_callback(self, on_done):
        """

        :param on_done:
        :return:
        """
        self.on_done = on_done

    def start(self):
        """

        :return:
        """
        self._start_dns_resolve()

    def _start_dns_resolve(self):
        """

        :return:
        """
        # fixme: use non-block dns resolve
        try:
            addr_list = socket.getaddrinfo(self.host, self.port, self.family, socket.SOCK_STREAM)
        except Exception as ex:
            addr_list = []
            logger.error(f"failed to dns resolve {self.host}, {ex}")

        if self.on_done:
            self.ev.call_soon(self.on_done, addr_list)
