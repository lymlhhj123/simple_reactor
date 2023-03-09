# coding: utf-8

import socket

from libreactor import logging
from libreactor import const

logger = logging.get_logger()


class BlockDNSResolver(object):

    def __init__(self, host, port, ev, on_done):
        """

        :param host:
        :param port:
        :param ev:
        :param on_done: callback
        """
        self.host = host
        self.port = port
        self.ev = ev

        self.on_done = on_done

        self._start_dns_resolve()

    def _start_dns_resolve(self):
        """

        :return:
        """
        try:
            addr_list = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            err_code = const.ErrorCode.OK
        except Exception as ex:
            addr_list = []
            err_code = const.ErrorCode.DNS_RESOLVE_FAILED
            logger.error(f"failed to dns resolve {self.host}, {ex}")

        if self.on_done:
            self.ev.call_soon(self.on_done, err_code, addr_list)
