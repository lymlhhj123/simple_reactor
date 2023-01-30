# coding: utf-8

import socket

from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class DNSResolver(object):

    def __init__(self, host, port, ev):
        """

        :param host:
        :param port:
        :param ev:
        """
        self.host = host
        self.port = port
        self.ev = ev

        self.on_result = None

    def set_callback(self, on_result):
        """

        :param on_result:
        :return:
        """
        self.on_result = on_result

    def start(self):
        """

        :return:
        """
        self._start_dns_resolve()

    def _start_dns_resolve(self):
        """

        :return:
        """
        # fixme: use non-block method
        try:
            addr_list = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            status = const.DNSResolvStatus.OK if addr_list else const.DNSResolvStatus.EMPTY
        except Exception as ex:
            addr_list = []
            status = const.DNSResolvStatus.FAILED
            logger.error(f"failed to dns resolve {self.host}, {ex}")

        if self.on_result:
            self.ev.call_soon(self.on_result, status, addr_list)
