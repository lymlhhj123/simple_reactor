# coding: utf-8

import os
import socket
import errno

from libreactor.channel import Channel
from libreactor import sock_util
from libreactor import utils
from libreactor.const import ConnectionState
from libreactor.const import ConnectionErr
from libreactor import logging

logger = logging.get_logger()

READ_SIZE = 8192


class TcpConnection(object):

    def __init__(self, sock, ctx, event_loop):
        """

        :param sock:
        :param ctx:
        :param event_loop:
        """
        self.sock = sock
        self.ctx = ctx
        self.ev = event_loop

        self.channel = Channel(sock.fileno(), event_loop)
        self.channel.set_read_callback(self._on_read_event)
        self.channel.set_write_callback(self._on_write_event)

        self.endpoint = None
        self.state = ConnectionState.DISCONNECTED
        self.write_buffer = b""
        self.protocol = None

        self.close_after_write = False
        self.linger_timer = None
        self.timeout_timer = None

        self.closed_callback = None

    def set_closed_callback(self, closed_callback):
        """

        :param closed_callback:
        :return:
        """
        self.closed_callback = closed_callback

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
            err_code = e.errno
            if err_code == errno.EISCONN:
                state = ConnectionState.CONNECTED
            elif err_code == errno.EINPROGRESS or err_code == errno.EALREADY:
                state = ConnectionState.CONNECTING
            else:
                state = ConnectionState.DISCONNECTED
        else:
            err_code = 0
            state = ConnectionState.CONNECTED

        if state == ConnectionState.CONNECTING:
            self.state = state
            self.channel.enable_writing()
            self.timeout_timer = self.ev.call_later(timeout, self._connection_timeout)
        elif state == ConnectionState.CONNECTED:
            self.connection_established()
        else:
            self._connection_failed(err_code)

    def connection_established(self):
        """

        client side connection
        :return:
        """
        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")
        self.state = ConnectionState.CONNECTED

        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        self.channel.enable_reading()

        self.protocol = self.ctx.build_protocol()
        self.protocol.connection_established(self, self.ev, self.ctx)

    def connection_made(self):
        """

        server side connection
        :return:
        """
        self.endpoint = sock_util.get_remote_addr(self.sock)

        self.state = ConnectionState.CONNECTED
        self.channel.enable_reading()

        self.protocol = self.ctx.build_protocol()
        self.protocol.connection_made(self, self.ev, self.ctx)

    def _connection_timeout(self):
        """

        client establish connection timeout
        :return:
        """
        logger.error(f"timeout to connect: {self.endpoint}")
        self._timeout_timer = None
        self._connection_error(ConnectionErr.TIMEOUT)

    def _connection_failed(self, err_code):
        """
        client failed to establish connection
        :param err_code:
        :return:
        """
        reason = os.strerror(err_code)
        logger.error(f"failed to connect {self.endpoint}, reason: {reason}")

        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        self._connection_error(ConnectionErr.CONNECT_FAILED)

    def _connection_error(self, error):
        """

        :param error:
        :return:
        """
        if self.protocol:
            self.protocol.connection_error(error)

        self._close_connection()

    def write(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        if self.ev.is_in_loop_thread():
            self._write_impl(bytes_)
        else:
            self.ev.call_soon(self._write_impl, bytes_)

    def _write_impl(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        if self.state == ConnectionState.DISCONNECTED or self.state == ConnectionState.DISCONNECTING:
            return

        # already call close() method, don't write data
        if self.close_after_write is True:
            logger.error("close method is already called, cannot write")
            return

        self.write_buffer += bytes_

        # still in connecting
        if self.state == ConnectionState.CONNECTING:
            return

        # try to write directly
        error = self._do_write()
        if error != ConnectionErr.OK:
            self._connection_error(error)
            return

        if self.write_buffer and not self.channel.writable():
            self.channel.enable_writing()

    def _on_write_event(self):
        """

        :return:
        """
        if self.state == ConnectionState.CONNECTING:
            self._handle_connect()

        if self.state != ConnectionState.CONNECTED:
            return

        if self.write_buffer:
            error = self._do_write()
            if error != ConnectionErr.OK:
                self._connection_error(error)
                return

        if self.write_buffer:
            return

        if self.close_after_write is True:
            self._close_connection()
            return

        if self.channel.writable():
            self.channel.disable_writing()

    def _do_write(self):
        """

        :return:
        """
        try:
            write_size = self.sock.send(self.write_buffer)
        except Exception as e:
            err_code = utils.errno_from_ex(e)
            return self._handle_rw_error(err_code)

        if write_size == 0:
            return ConnectionErr.PEER_CLOSED

        self.write_buffer = self.write_buffer[write_size:]
        return ConnectionErr.OK

    def _on_read_event(self):
        """

        :return:
        """
        if self.state == ConnectionState.CONNECTING:
            self._handle_connect()

        if self.state != ConnectionState.CONNECTED:
            return

        error = self._do_read()
        if error != ConnectionErr.OK:
            self._connection_error(error)
            return

    def _do_read(self):
        """

        :return:
        """
        while True:
            try:
                data = self.sock.recv(READ_SIZE)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                return self._handle_rw_error(err_code)

            if not data:
                return ConnectionErr.PEER_CLOSED

            self._data_received(data)

    def _handle_connect(self):
        """

        :return:
        """
        err_code = sock_util.get_sock_error(self.sock)
        if err_code != 0:
            self._connection_failed(err_code)
            return

        self.channel.disable_writing()
        self.connection_established()

    def _handle_rw_error(self, err_code):
        """

        :param err_code:
        :return:
        """
        if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
            return ConnectionErr.OK

        reason = os.strerror(err_code)
        logger.error(f"connection error with {self.endpoint}, reason: {reason}")

        if err_code == errno.EPIPE:
            return ConnectionErr.BROKEN_PIPE
        else:
            return ConnectionErr.UNKNOWN

    def _data_received(self, data):
        """

        :param data:
        :return:
        """
        self.protocol.data_received(data)

    def close(self, so_linger=False, delay=2):
        """

        :param so_linger: like socket so-linger option
        :param delay: sec
        :return:
        """
        assert delay > 0
        if self.ev.is_in_loop_thread():
            self._close_in_loop(so_linger, delay)
        else:
            self.ev.call_soon(self._close_in_loop, so_linger, delay)

    def _close_in_loop(self, so_linger, delay):
        """

        :param so_linger:
        :param delay: sec
        :return:
        """
        if not self.write_buffer:
            self._close_connection()
            return

        if not so_linger:
            # wait write buffer empty. close connection until write buffer
            # is empty or error happened; otherwise, delay close connection
            # after `delay` second and drop write buffer if it has.
            self.close_after_write = True
            return

        logger.warning("write buffer is not empty, delay to close connection")
        self.linger_timer = self.ev.call_later(delay, self._delay_close)

    def _delay_close(self):
        """

        :return:
        """
        if self.write_buffer:
            logger.warning("force close connection and drop write buffer")

        self._close_connection()

    def _close_connection(self):
        """

        :return:
        """
        if self.state == ConnectionState.DISCONNECTING or self.state == ConnectionState.DISCONNECTED:
            return

        self.state = ConnectionState.DISCONNECTING

        if self.linger_timer:
            self.linger_timer.cancel()

        if self.closed_callback:
            self.closed_callback(self)

        self.write_buffer = b""
        self.channel.disable_all()

        # close on next loop
        self.ev.call_soon(self._close_force)

    def _close_force(self):
        """

        :return:
        """
        self.channel.close()

        self.state = ConnectionState.DISCONNECTED
        self.sock = None

        self.protocol = None
        self.ctx = None

        self.linger_timer = None
        self.closed_callback = None
