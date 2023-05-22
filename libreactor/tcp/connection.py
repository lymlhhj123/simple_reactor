# coding: utf-8

import socket

from . import state
from ..core import Channel
from ..common import logging
from ..common import utils
from ..common import sock_helper
from ..common import error


logger = logging.get_logger()

READ_SIZE = 8192


class Connection(object):

    def __init__(self, sock, ctx, ev):
        """

        :param sock:
        :param ctx:
        :param ev:
        """
        self.sock = sock
        self.ctx = ctx
        self.ev = ev

        self.channel = Channel(sock.fileno(), ev)
        self.channel.set_read_callback(self._on_read_event)
        self.channel.set_write_callback(self._on_write_event)

        self.endpoint = None
        self.state = state.DISCONNECTED
        self.write_buffer = bytearray()
        self.protocol = None

        self._conn_lost = 0
        self.closing = False
        self.timeout_timer = None

    def fileno(self):
        """

        :return:
        """
        return self.sock.fileno()

    def try_open(self, endpoint, timeout=10):
        """

        :param endpoint:
        :param timeout:
        :return:
        """
        assert self.ev.is_in_loop_thread()
        self.endpoint = endpoint

        try:
            self.sock.connect(endpoint)
        except socket.error as e:
            code = utils.errno_from_ex(e)
        else:
            code = error.OK

        if code == error.EISCONN or code == error.OK:
            self.connection_established()
        elif code == error.EINPROGRESS or code == error.EALREADY:
            self._wait_connection_established(timeout)
        else:
            self._connection_failed(code)

    def _wait_connection_established(self, timeout):
        """

        :return:
        """
        self.state = state.CONNECTING
        self.channel.enable_writing()
        self.timeout_timer = self.ev.call_later(timeout, self._connection_failed, error.ETIMEDOUT)

    def connection_established(self):
        """
        client side established connection
        :return:
        """
        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            err_code = error.Reason(error.SELF_CONNECT)
            self._connection_lost(err_code)
            return

        self._cancel_timeout_timer()

        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")
        self.state = state.CONNECTED
        self.channel.enable_reading()

        self.protocol = self._build_protocol()
        self.protocol.connection_established(self)
        self.ctx.connection_established(self.protocol)

    def connection_made(self, addr):
        """
        server side accept new connection
        :param addr:
        :return:
        """
        self.endpoint = addr

        self.state = state.CONNECTED
        self.channel.enable_reading()

        self.protocol = self._build_protocol()
        self.protocol.connection_made(self)
        self.ctx.connection_made(self.protocol)

    def _build_protocol(self):
        """

        :return:
        """
        protocol = self.ctx.build_protocol()
        protocol.ctx = self.ctx
        protocol.event_loop = self.ev
        return protocol

    def _connection_failed(self, err_code):
        """
        client failed to establish connection
        :param err_code:
        :return:
        """
        self._cancel_timeout_timer()
        self._force_close(error.Reason(err_code))

    def _cancel_timeout_timer(self):
        """

        :return:
        """
        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        assert self.ev.is_in_loop_thread()

        if self._conn_lost:
            return

        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        # still in connecting
        if self.state == state.CONNECTING:
            self.write_buffer.extend(data)
            return

        # try to write directly
        if not self.write_buffer:
            code, write_size = self.channel.write(data)
            if error.is_bad_error(code):
                self._force_close(error.Reason(code))
                return

            data = data[write_size:]
            if not data:
                return

            self.channel.enable_writing()

        self.write_buffer.extend(data)

    def _on_write_event(self):
        """

        :return:
        """
        if self.state == state.CONNECTING:
            self._handle_connect()

        if self.state != state.CONNECTED:
            return

        if self.write_buffer:
            code, write_size = self.channel.write(self.write_buffer)
            if error.is_bad_error(code):
                self._force_close(error.Reason(code))
                return

            del self.write_buffer[:write_size]

        if not self.write_buffer and self.closing is True:
            self._force_close(error.Reason(error.USER_CLOSED))
            return

        if not self.write_buffer and self.channel.writable():
            self.channel.disable_writing()

    def _on_read_event(self):
        """

        :return:
        """
        if self._conn_lost:
            return

        if self.state == state.CONNECTING:
            self._handle_connect()

        if self.state != state.CONNECTED:
            return

        code = self._do_read()
        if error.is_bad_error(code):
            self._force_close(error.Reason(code))

    def _do_read(self):
        """

        :return:
        """
        err_code, data = self.channel.read(READ_SIZE)
        if data:
            self.protocol.data_received(data)

        return err_code

    def _handle_connect(self):
        """

        :return:
        """
        code = sock_helper.get_sock_error(self.sock)
        if error.is_bad_error(code):
            self._connection_failed(code)
            return

        self.channel.disable_writing()
        self.connection_established()

    def abort(self):
        """force to close connection

        :return:
        """
        assert self.ev.is_in_loop_thread()
        reason = error.Reason(error.USER_ABORT)
        self._force_close(reason)

    def _force_close(self, reason):
        """

        :param reason:
        :return:
        """
        if self._conn_lost:
            return

        if self.write_buffer:
            self.write_buffer.clear()

        if not self.closing:
            self.closing = True

        self.channel.disable_all()

        self._conn_lost += 1
        self.ev.call_soon(self._connection_lost, reason)

    def close(self):
        """

        :return:
        """
        assert self.ev.is_in_loop_thread()

        if self.closing is True:
            return

        self.closing = True
        self.channel.disable_reading()

        # write buffer is empty, close it
        if not self.write_buffer:
            self.channel.disable_writing()

            self._conn_lost += 1
            reason = error.Reason(error.USER_CLOSED)
            self.ev.call_soon(self._connection_lost, reason)

    def _connection_lost(self, reason):
        """

        :return:
        """
        try:
            if self.protocol:
                self.protocol.connection_lost(reason)

            self.ctx.connection_lost(self, reason)
        finally:
            self.channel.close()
            self.sock.close()

            self.channel = None
            self.protocol = None
            self.ctx = None
            self.sock = None
