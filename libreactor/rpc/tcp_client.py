# coding: utf-8

import socket
import random

from .tcp_connector import TcpConnector
# from ..dns_resolver import DNSResolver
from libreactor import const
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, event_loop, ctx, timeout=10, is_ipv6=False, auto_reconnect=False):
        """

        :param host:
        :param port:
        :param event_loop:
        :param ctx:
        :param timeout:
        :param is_ipv6:
        :param auto_reconnect:
        """
        self.host = host
        self.port = port
        self.event_loop = event_loop
        self.ctx = ctx
        self.timeout = timeout
        self.is_ipv6 = is_ipv6
        self.auto_reconnect = auto_reconnect

    def start(self):
        """

        :return:
        """
        self.event_loop.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        self._try_connect(family, (self.host, self.port))
        # resolver = DNSResolver(self.host, self.port, self.event_loop, self.is_ipv6)
        # resolver.set_callback(on_done=self._dns_done)
        # resolver.start()

    def _dns_done(self, status, addr_list):
        """

        :param status:
        :param addr_list:
        :return:
        """
        assert self.event_loop.is_in_loop_thread()

        if status == const.DNSResolvStatus.OK:
            af, _, _, _, sa = addr_list[0]
            self._try_connect(af, sa)
        else:
            self._reconnect()

    def _try_connect(self, family, endpoint):
        """

        :param family:
        :param endpoint:
        :return:
        """
        print("start connect")
        connector = TcpConnector(family, endpoint, self.event_loop, self.ctx, self.timeout)
        connector.set_closed_callback(closed_callback=self._on_closed)
        connector.start_connect()

    def _on_closed(self):
        """

        :return:
        """
        logger.info(f"connection closed with server: {self.host, self.port}")
        if self.auto_reconnect:
            self._reconnect()

    def _reconnect(self):
        """

        :return:
        """
        delay = random.random() * 5
        logger.info(f"reconnect to server after {delay} seconds")
        self.event_loop.call_later(delay, self._start_in_loop)
