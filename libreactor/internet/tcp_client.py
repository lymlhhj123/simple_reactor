# coding: utf-8

import socket
import random

from ..const import ErrorCode
from .tcp_connector import TcpConnector
# from ..dns_resolver import DNSResolver
from libreactor import logging

logger = logging.get_logger()


class TcpClient(object):

    def __init__(self, host, port, ev, ctx, is_ipv6, timeout=10, auto_reconnect=False):
        """

        :param host:
        :param port:
        :param ev:
        :param ctx:
        :param is_ipv6:
        :param timeout:
        :param auto_reconnect:
        """
        self.host = host
        self.port = port
        self.ev = ev
        self.ctx = ctx
        self.timeout = timeout
        self.is_ipv6 = is_ipv6
        self.auto_reconnect = auto_reconnect

    def start(self):
        """

        :return:
        """
        self.ev.call_soon(self._start_in_loop)

    def _start_in_loop(self):
        """

        :return:
        """
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        self._try_connect(family, (self.host, self.port))
        # resolver = DNSResolver(self.host, self.port, family, self.ev)
        # resolver.set_done_callback(self._dns_done)
        # resolver.start()

    def _dns_done(self, addr_list):
        """

        :param addr_list:
        :return:
        """
        assert self.ev.is_in_loop_thread()

        if addr_list:
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
        connector = TcpConnector(family, endpoint, self.ev, self.ctx, self.timeout)
        connector.set_error_callback(self._connection_error)
        connector.set_failure_callback(self._connection_failed)
        connector.start_connect()

    def _connection_error(self, err_code):
        """

        :return:
        """
        reason = ErrorCode.str_error(err_code)
        logger.error(f"error happened with {self.host}:{self.port}, reason: {reason}")

        if self.auto_reconnect:
            self._reconnect()

        self.ctx.connection_error()

    def _connection_failed(self, err_code):
        """

        :return:
        """
        reason = ErrorCode.str_error(err_code)
        logger.error(f"failed to connect {self.host}:{self.port}, reason: {reason}")

        if self.auto_reconnect:
            self._reconnect()

        self.ctx.connection_error()

    def _reconnect(self):
        """

        :return:
        """
        delay = random.random() * 5
        logger.info(f"reconnect to server after {delay} seconds")
        self.ev.call_later(delay, self._start_in_loop)
        

class TcpV4Client(TcpClient):
    
    def __init__(self, host, port, ev, ctx, timeout=10, auto_reconnect=False):
        """
        
        :param host: 
        :param port: 
        :param ev: 
        :param ctx: 
        :param timeout: 
        :param auto_reconnect: 
        """
        super(TcpV4Client, self).__init__(host, port, ev, ctx, False, timeout, auto_reconnect)


class TcpV6Client(TcpClient):

    def __init__(self, host, port, ev, ctx, timeout=10, auto_reconnect=False):
        """

        :param host:
        :param port:
        :param ev:
        :param ctx:
        :param timeout:
        :param auto_reconnect:
        """
        super(TcpV6Client, self).__init__(host, port, ev, ctx, True, timeout, auto_reconnect)
