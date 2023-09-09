# coding: utf-8

import socket

from ..common import sock_helper
from ..common import fd_helper
from ..common import error
from ..common import logging
from ..core import Channel
from ..common import utils
from .transport import Client

logger = logging.get_logger()


class Connector(object):

    def __init__(self, family, endpoint, ctx, ev, options):
        """

        :param family:
        :param endpoint:
        :param ctx:
        :param ev:
        :param options:
        """
        self.family = family
        self.endpoint = endpoint
        self.ctx = ctx
        self.ev = ev
        self.options = options

        self.sock = None
        self.connect_channel = None
        self.connect_timer = None

    def connect(self):
        """

        :return:
        """
        sock = socket.socket(self.family, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)

        if self.options.tcp_no_delay:
            sock_helper.set_tcp_no_delay(sock)

        if self.options.tcp_keepalive:
            sock_helper.set_tcp_keepalive(sock)

        fd_helper.close_on_exec(sock.fileno(), self.options.close_on_exec)

        self._start_connect(sock)

    def _start_connect(self, sock):
        """

        :param sock:
        :return:
        """
        assert self.ev.is_in_loop_thread()

        try:
            sock.connect(self.endpoint)
        except socket.error as e:
            code = utils.errno_from_ex(e)
        else:
            code = error.OK

        if code == error.EISCONN or code == error.OK:
            self._connection_established()
        elif code == error.EINPROGRESS or code == error.EALREADY:
            self._wait_connection_established(sock)
        else:
            self._connection_failed(code)

    def _wait_connection_established(self, sock):
        """

        :return:
        """
        channel = Channel(sock.fileno(), self.ev)
        channel.set_read_callback(self._do_connect)
        channel.set_write_callback(self._do_connect)
        channel.enable_writing()

        timeout = self.options.connect_timeout
        self.connect_timer = self.ev.call_later(timeout, self._connection_failed, error.ETIMEDOUT)

        self.sock = sock
        self.connect_channel = channel

    def _do_connect(self):
        """

        :return:
        """

        code = sock_helper.get_sock_error(self.sock)
        if error.is_bad_error(code):
            self._connection_failed(code)
            return

        self.connect_channel.disable_writing()
        self._connection_established()

    def _connection_established(self):
        """
        client side established connection
        :return:
        """
        self._cancel_timeout_timer()

        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            reason = error.Reason(error.SELF_CONNECT)
            self._connection_failed(reason)
            return

        self.connect_channel.close()
        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")

        conn = Client(self.sock, self.ctx, self.ev, self)

        remote_addr = sock_helper.get_remote_addr(self.sock)
        conn.connection_established(remote_addr)

        del self.sock
        del self.connect_channel

    def _connection_failed(self, reason):
        """
        client failed to establish connection
        :param reason:
        :return:
        """
        self._cancel_timeout_timer()

        self.connect_channel.close()
        self.sock.close()

        del self.sock
        del self.connect_channel

        self.ctx.connection_failed(self, reason)

    def _cancel_timeout_timer(self):
        """

        :return:
        """
        if self.connect_timer:
            self.connect_timer.cancel()
            self.connect_timer = None

    def connection_lost(self, reason):
        """

        :param reason:
        :return:
        """
        self.ctx.connection_lost(self, reason)
