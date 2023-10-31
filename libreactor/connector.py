# coding: utf-8

import ssl
import socket

from .channel import Channel
from .connection import Connection
from . import futures
from . import sock_helper
from . import fd_helper
from . import ssl_helper
from . import utils
from . import error
from . import log

logger = log.get_logger()


class Connector(object):

    def __init__(self, loop, family, endpoint, proto_factory, options):

        self.loop = loop
        self.family = family
        self.endpoint = endpoint
        self.proto_factory = proto_factory
        self.options = options

        self.ssl_options = options.ssl_options
        self.need_ssl_handshake = True if self.ssl_options else False

        self.sock = None
        self.connect_channel = None
        self.connect_timer = None

        self.connect_fut = None

    def connect(self):
        """

        :return:
        """
        self.sock = self._create_sock()

        self.connect_fut = futures.create_future()

        self._do_connect()

        return self.connect_fut

    def _create_sock(self):
        """create connect socket"""
        sock = socket.socket(self.family, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)

        if self.options.tcp_no_delay:
            sock_helper.set_tcp_no_delay(sock)

        if self.options.tcp_keepalive:
            sock_helper.set_tcp_keepalive(sock)

        fd_helper.close_on_exec(sock.fileno(), self.options.close_on_exec)

        return sock

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
        channel = Channel(self.sock.fileno(), self.loop)
        channel.set_read_callback(self._do_connect)
        channel.set_write_callback(self._do_connect)
        channel.enable_writing()

        timeout = self.options.connect_timeout
        if timeout and timeout > 0:
            self.connect_timer = self.loop.call_later(timeout, self._connection_failed, error.ETIMEDOUT)

        self.connect_channel = channel

    def _connection_established(self):
        """client side established connection"""
        self._cancel_timeout_timer()

        self.connect_channel.disable_writing()

        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            self._connection_failed(error.ESELFCONNECTED)
            return

        # socket connected and start ssl handshake
        if self.ssl_options and self.need_ssl_handshake:
            self.need_ssl_handshake = False
            self._start_ssl()
            return

        self.connect_channel.close()
        self.connect_channel = None
        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")

        sock, self.sock = self.sock, None

        protocol = self.proto_factory()
        conn = Connection(sock, protocol, self.loop)
        remote_addr = sock_helper.get_remote_addr(sock)
        conn.connection_established(remote_addr)

        fut, self.connect_fut = self.connect_fut, None
        futures.future_set_result(fut, protocol)

    def _start_ssl(self):
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
        self.connect_channel.set_read_callback(self._do_ssl_handshake)

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

        fut, self.connect_fut = self.connect_fut, None
        futures.future_set_exception(fut, error.Failure(errcode))

    def _cancel_timeout_timer(self):
        """cancel connect timeout timer"""
        if self.connect_timer:
            self.connect_timer.cancel()
            self.connect_timer = None
