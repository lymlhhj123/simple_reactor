# coding: utf-8

import random

from .tcp_connector import TcpConnector
from ..dns_resolver import DNSResolver
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
        resolver = DNSResolver(self.host, self.port, self.event_loop, self.is_ipv6)
        resolver.set_callback(on_result=self._dns_done)
        resolver.start()

    def _dns_done(self, status, addr_list):
        """

        :param status:
        :param addr_list:
        :return:
        """
        assert self.event_loop.is_in_loop_thread()

        if status == const.DNSResolvStatus.OK:
            af, _, _, _, sa = addr_list[0]
            connector = TcpConnector(af, sa, self.event_loop, self.ctx, self.timeout)
            connector.set_callback(on_closed=self._on_closed)
            connector.start_connect()
        else:
            self._reconnect()

    def _on_closed(self):
        """

        :return:
        """
        logger.info(f"connection closed with server: {self.host, self.port}")
        self._reconnect()

    def _reconnect(self):
        """

        :return:
        """
        if not self.auto_reconnect:
            return

        delay = random.random() * 5
        logger.info(f"reconnect to server after {delay} seconds")
        self.event_loop.call_later(delay, self._start_in_loop)
