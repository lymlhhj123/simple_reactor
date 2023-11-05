# coding: utf-8

import ssl
import socket

from .channel import Channel
from .connection import Connection
from . import futures
from . import sock_helper
from . import ssl_helper
from . import utils
from . import error
from . import log

logger = log.get_logger()


class Connector(object):

    def __init__(self, loop, sock, endpoint, proto_factory, waiter, factory, options, ssl_options):

        self.loop = loop
        self.sock = sock
        self.endpoint = endpoint
        self.proto_factory = proto_factory
        self.factory = factory
        self.options = options

        self.waiter = waiter

        self._ssl_handshaking = True if ssl_options else False
        self.ssl_options = ssl_options

        self.connect_timer = None

        self.connect_channel = Channel(self.sock.fileno(), self.loop)

    def connect(self):
        """

        :return:
        """
        self._do_connect()

    def _do_connect(self):
        """

        :return:
        """
        try:
            self.sock.connect(self.endpoint)
        except socket.error as e:
            code = utils.errno_from_ex(e)
        else:
            code = error.OK

        if code in [error.EISCONN, error.OK]:
            self._connection_established()
        elif code in [error.EINPROGRESS, error.EALREADY]:
            self._wait_connection_established()
        else:
            self._connection_failed(code)

    def _wait_connection_established(self):
        """wait socket connected or failed"""
        self.connect_channel.set_read_callback(self._do_connect)
        self.connect_channel.set_write_callback(self._do_connect)
        self.connect_channel.enable_writing()

        timeout = self.options.connect_timeout
        if timeout and timeout > 0:
            self.connect_timer = self.loop.call_later(timeout, self._connection_failed, error.ETIMEDOUT)

    def _connection_established(self):
        """client side established connection"""
        self._cancel_timeout_timer()

        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            self._connection_failed(error.ESELFCONNECTED)
            return

        # socket connected and start ssl handshake
        if self.ssl_options and self._ssl_handshaking:
            self._ssl_handshaking = False
            self._start_tls()
            return

        self.connect_channel.disable_writing()
        self.connect_channel.close()
        self.connect_channel = None
        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")

        sock, self.sock = self.sock, None

        protocol = self.proto_factory()
        conn = Connection(sock, protocol, self.loop)
        conn.connection_established(self.endpoint, self.factory)

        fut, self.waiter = self.waiter, None
        futures.future_set_result(fut, protocol)

    def _start_tls(self):
        """wrap socket to ssl, start handshake"""
        context = ssl_helper.ssl_client_context()
        self.sock = ssl_helper.ssl_wrap_socket(
            ssl_context=context,
            sock=self.sock,
            server_hostname=self.ssl_options.server_hostname,
            server_side=False
        )

        self._do_ssl_handshake()

    def _do_ssl_handshake(self):
        """if enable ssl, then do handshake after succeed to connect"""
        try:
            self.sock.do_handshake()
        except ssl.SSLError as e:
            errcode = utils.errno_from_ex(e)
            if errcode in error.IO_WOULD_BLOCK:
                self.connect_channel.set_read_callback(self._do_ssl_handshake)
                self.connect_channel.set_write_callback(self._do_ssl_handshake)
                self.connect_channel.enable_writing()
                return

            self._connection_failed(error.ESSL)
        except socket.error as e:
            errcode = utils.errno_from_ex(e)
            self._connection_failed(errcode)
        except Exception as e:
            errcode = utils.errno_from_ex(e)
            self._connection_failed(errcode)
        else:
            self._connection_established()

    def _connection_failed(self, errcode):
        """client failed to establish connection"""
        self._cancel_timeout_timer()

        self.connect_channel.disable_writing()
        self.connect_channel.close()
        self.sock.close()

        self.sock = None
        self.connect_channel = None

        fut, self.waiter = self.waiter, None
        futures.future_set_exception(fut, error.Failure(errcode))

    def _cancel_timeout_timer(self):
        """cancel connect timeout timer"""
        if self.connect_timer:
            self.connect_timer.cancel()
            self.connect_timer = None
