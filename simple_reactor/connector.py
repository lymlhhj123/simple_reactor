# coding: utf-8

import os
import errno

from .channel import Channel
from .connection import Connection
from . import futures
from . import sock_helper
from . import ssl_helper
from . import utils
from . import errors
from . import log

logger = log.get_logger()

CONNECT_OK = 0
CONNECT_FAILED = 1
CONNECT_IN_PROGRESS = 2

SSL_HANDSHAKE_OK = 0
SSL_HANDSHAKE_FAILED = 1
SSL_HANDSHAKE_IN_PROGRESS = 2


class Connector(object):

    def __init__(self, loop, sock, endpoint, proto_factory, waiter, factory, options, ssl_options):
        """stream connection connector"""
        self.loop = loop
        self.sock = sock
        self.endpoint = endpoint
        self.proto_factory = proto_factory
        self.factory = factory
        self.options = options

        self.waiter = waiter

        self.ssl_options = ssl_options

        self.connect_channel = Channel(self.sock.fileno(), self.loop)

        self.connect_timer = None
        self.handshake_timer = None

    def connect(self):
        """start connect endpoint"""
        if self._do_connect() == CONNECT_IN_PROGRESS:
            self._wait_connection_finished(self.options.connect_timeout)

    def _do_connect(self):
        """setup socket connect"""
        try:
            self.sock.connect(self.endpoint)
        except Exception as e:
            code = utils.errno_from_ex(e)
        else:
            code = errors.OK

        if code in [errno.EISCONN, errors.OK]:
            self._connection_established()
            return CONNECT_OK
        elif code in [errno.EINPROGRESS, errno.EALREADY]:
            return CONNECT_IN_PROGRESS
        else:
            exc = ConnectionError(f"Failed to connect: {self.endpoint}, err: {os.strerror(code)}")
            self._connection_failed(exc)
            return CONNECT_FAILED

    def _wait_connection_finished(self, connect_timeout):
        """wait socket connected or failed"""
        self.connect_channel.set_read_callback(self._do_connect)
        self.connect_channel.set_write_callback(self._do_connect)
        self.connect_channel.enable_writing()

        if connect_timeout > 0:
            exc = TimeoutError(f"Timeout to connect: {self.endpoint}")
            self.connect_timer = self.loop.call_later(connect_timeout, self._connection_failed, exc)

    def _connection_established(self):
        """client side established connection"""
        self._cancel_connect_timer()

        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            exc = ConnectionError("sock is self connect")
            self._connection_failed(exc)
            return

        # start ssl handshake
        if self.ssl_options:
            try:
                self._start_tls(self.ssl_options)
            except Exception as e:
                self._connection_failed(e)
        else:
            self._connection_ok()

    def _start_tls(self, ssl_options):
        """wrap socket to ssl, start handshake"""
        if ssl_options.ssl_client_ctx:
            ssl_context = ssl_options.ssl_client_ctx
        else:
            ssl_context = ssl_helper.ssl_client_context()

        self.sock = ssl_helper.ssl_wrap_socket(
            ssl_context=ssl_context,
            sock=self.sock,
            server_hostname=ssl_options.server_hostname,
            server_side=False
        )

        if self._do_ssl_handshake() == SSL_HANDSHAKE_IN_PROGRESS:
            self._wait_handshake_finished(ssl_options.handshake_timeout)

    def _do_ssl_handshake(self):
        """if enable ssl, then do handshake after succeed to connect"""
        try:
            self.sock.do_handshake()
        except Exception as e:
            errcode = utils.errno_from_ex(e)
            if errcode not in errors.IO_WOULD_BLOCK:
                exc = ConnectionError(f"Failed to verify ssl, {e}")
                self._connection_failed(exc)
                return SSL_HANDSHAKE_FAILED
            else:
                return SSL_HANDSHAKE_IN_PROGRESS
        else:
            self._connection_ok()
            return SSL_HANDSHAKE_OK

    def _wait_handshake_finished(self, handshake_timeout):
        """wait handshake succeed or failed"""
        self.connect_channel.set_read_callback(self._do_ssl_handshake)
        self.connect_channel.set_write_callback(self._do_ssl_handshake)
        self.connect_channel.enable_writing()

        if handshake_timeout > 0:
            exc = TimeoutError(f"Timeout to do ssl handshake: {self.endpoint}")
            self.handshake_timer = self.loop.call_later(handshake_timeout, self._connection_failed, exc)

    def _connection_ok(self):
        """the final callback when connection is established"""
        self._cancel_handshake_timer()

        self.connect_channel.disable_all()
        self.connect_channel.close()
        self.connect_channel = None
        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")

        sock, self.sock = self.sock, None

        protocol = self.proto_factory()
        conn = Connection(sock, protocol, self.loop)
        conn.connection_established(self.endpoint, self.factory)

        fut, self.waiter = self.waiter, None
        futures.future_set_result(fut, protocol)

    def _connection_failed(self, exc):
        """client failed to establish connection"""
        self._cancel_connect_timer()
        self._cancel_handshake_timer()

        self.connect_channel.disable_writing()
        self.connect_channel.close()
        sock_helper.close_sock(self.sock)

        self.sock = None
        self.connect_channel = None

        waiter, self.waiter = self.waiter, None
        futures.future_set_exception(waiter, exc)

    def _cancel_connect_timer(self):
        """cancel connect timeout timer"""
        if self.connect_timer:
            self.connect_timer.cancel()
            self.connect_timer = None

    def _cancel_handshake_timer(self):
        """cancel handshake timer"""
        if self.handshake_timer:
            self.handshake_timer.cancel()
            self.handshake_timer = None
