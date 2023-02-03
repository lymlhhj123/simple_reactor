# coding: utf-8

import socket

from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class DNSResolver(object):

    def __init__(self, host, port, ev, is_ipv6=False):
        """

        :param host:
        :param port:
        :param ev:
        :param is_ipv6:
        """
        self.host = host
        self.port = port
        self.ev = ev
        self.is_ipv6 = is_ipv6

        self.on_done = None

    def set_callback(self, on_done):
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
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        try:
            addr_list = socket.getaddrinfo(self.host, self.port, family, socket.SOCK_STREAM)
            status = const.DNSResolvStatus.OK if addr_list else const.DNSResolvStatus.EMPTY
        except Exception as ex:
            addr_list = []
            status = const.DNSResolvStatus.FAILED
            logger.error(f"failed to dns resolve {self.host}, {ex}")

        if self.on_done:
            self.ev.call_soon(self.on_done, status, addr_list)
