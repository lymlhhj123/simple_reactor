# coding: utf-8

import errno
from functools import partial

from .connection import Connection
from .channel import Channel
from . import sock_helper
from . import fd_helper
from . import ssl_helper
from . import utils
from . import errors
from . import log

logger = log.get_logger()


class Acceptor(object):

    def __init__(self, loop, socks, proto_factory, factory, options, ssl_options):

        self.loop = loop
        self.socks = socks
        self.proto_factory = proto_factory
        self.options = options
        self.factory = factory
        self.ssl_options = ssl_options

        self.placeholder = open("/dev/null")
        self.channel_map = {}

        self._ssl_context = self._create_ssl_context()

    def _create_ssl_context(self):
        """create server side ssl context"""
        if not self.ssl_options:
            return

        context = ssl_helper.ssl_server_context()
        cert_file, key_file = self.ssl_options.cert_file, self.ssl_options.key_file
        if cert_file or key_file:
            context.load_cert_chain(cert_file, key_file)

        return context

    def start(self):
        """start stream msg server"""
        for sock in self.socks:
            channel = Channel(sock.fileno(), self.loop)

            accept_fn = partial(self._do_accept, sock)
            channel.set_read_callback(accept_fn)
            channel.enable_reading()

            self.channel_map[sock.fileno()] = channel

    def _do_accept(self, accept_sock):
        """accept incoming connection"""
        while True:
            try:
                sock, addr = accept_sock.accept()
            except Exception as e:
                errcode = utils.errno_from_ex(e)
                if errcode in errors.IO_WOULD_BLOCK:
                    break
                elif errcode == errno.EMFILE:
                    self._too_many_open_file(accept_sock)
                elif errcode in [errno.ENFILE, errno.ENOMEM, errno.ECONNABORTED]:
                    break
                else:
                    logger.error("unknown error happened on do accept: %s", e)
                    self._do_accept_error(accept_sock)
                    break
            else:
                self._on_new_connection(sock, addr)

    def _too_many_open_file(self, accept_sock):
        """close placeholder fd and accept connection"""
        logger.error("too many open file, accept and close connection")
        self.placeholder.close()
        sock, _ = accept_sock.accept()
        sock_helper.close_sock(sock)
        self._placeholder = open("/dev/null")

    def _do_accept_error(self, accept_sock):
        """error happened when do accept"""
        self.socks.remove(accept_sock)
        fd = accept_sock.fileno()
        channel = self.channel_map.pop(fd)

        channel.disable_reading()
        channel.close()
        accept_sock.close()

    def _on_new_connection(self, sock, addr):
        """server accept new connection"""
        logger.info(f"accept connection: {addr}, fd: {sock.fileno()}")

        if self._ssl_context:
            try:
                ssl_helper.ssl_wrap_socket(self._ssl_context, sock, server_side=True)
            except Exception as e:
                logger.exception(f"failed to warp ssl socket, {e}")
                sock_helper.close_sock(sock)
                return

        sock_helper.set_sock_async(sock)

        if sock_helper.is_tcp_sock(sock):
            if self.options.tcp_no_delay:
                sock_helper.set_tcp_no_delay(sock)

            if self.options.tcp_keepalive:
                sock_helper.set_tcp_keepalive(sock)

        fd_helper.close_on_exec(sock.fileno(), self.options.close_on_exec)

        protocol = self.proto_factory()
        conn = Connection(sock, protocol, self.loop)

        self.loop.call_soon(conn.connection_made, addr, self.factory)
