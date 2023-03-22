# coding: utf-8

import socket
import errno

from libreactor.channel import Channel
from libreactor import sock_helper
from libreactor import utils
from libreactor.const import ErrorCode
from libreactor.const import ConnectionState
from libreactor import logging

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
        self.state = ConnectionState.DISCONNECTED
        self.write_buffer = b""
        self.protocol = None

        self.error_code = ErrorCode.OK

        self.close_after_write = False
        self.linger_timer = None
        self.timeout_timer = None

    def fileno(self):
        """

        :return:
        """
        return self.sock.fileno()

    def errno(self):
        """

        :return:
        """
        return self.error_code

    def str_error(self):
        """

        :return:
        """
        return ErrorCode.str_error(self.error_code)

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
            err_code = utils.errno_from_ex(e)
        else:
            err_code = ErrorCode.OK

        if err_code == errno.EISCONN or err_code == ErrorCode.OK:
            self.connection_established()
        elif err_code == errno.EINPROGRESS or err_code == errno.EALREADY:
            self._wait_connection_established(timeout)
        else:
            self._connection_failed(err_code)

    def _wait_connection_established(self, timeout):
        """

        :return:
        """
        self.state = ConnectionState.CONNECTING
        self.channel.enable_writing()
        self.timeout_timer = self.ev.call_later(timeout, self._connection_timeout)

    def connection_established(self):
        """
        client side established connection
        :return:
        """
        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            self._close_connection()
            return

        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")
        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        self.state = ConnectionState.CONNECTED
        self.channel.enable_reading()

        self.protocol = protocol = self._build_protocol()
        protocol.connection_established()
        self.ctx.connection_established(protocol)

    def connection_made(self, addr):
        """
        server side accept new connection
        :param addr:
        :return:
        """
        self.endpoint = addr

        self.state = ConnectionState.CONNECTED
        self.channel.enable_reading()

        self.protocol = protocol = self._build_protocol()
        self.protocol.connection_made()
        self.ctx.connection_made(protocol)

    def _build_protocol(self):
        """

        :return:
        """
        protocol = self.ctx.build_protocol()
        protocol.connection = self
        protocol.ctx = self.ctx
        protocol.event_loop = self.ev
        return protocol

    def _connection_timeout(self):
        """
        client establish connection timeout
        :return:
        """
        self._timeout_timer = None
        self._connection_failed(ErrorCode.TIMEOUT)

    def _connection_failed(self, err_code):
        """
        client failed to establish connection
        :param err_code:
        :return:
        """
        self.error_code = err_code

        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        self._close_connection()
        self.ctx.connection_failure(self)

    def _connection_error(self, err_code):
        """
        error happened when on read/write
        :return:
        """
        self.error_code = err_code

        self._close_connection()

        self.protocol.connection_error()
        self.ctx.connection_error(self)

    def _connection_closed(self):
        """

        :return:
        """
        if self.protocol:
            self.protocol.connection_closed()

        self.ctx.connection_closed(self)

    def write(self, data: bytes):
        """

        :param data:
        :return:
        """
        if not isinstance(data, bytes):
            logger.error(f"only accept bytes, not {type(data)}")
            return

        if self.ev.is_in_loop_thread():
            self._write_in_loop(data)
        else:
            self.ev.call_soon(self._write_in_loop, data)

    def _write_in_loop(self, data):
        """

        :param data:
        :return:
        """
        if self._connection_will_be_closed():
            return

        # already call close() method, don't write data
        if self.close_after_write is True:
            logger.error("close method is already called, cannot write")
            return

        self.write_buffer += data

        # still in connecting
        if self.state == ConnectionState.CONNECTING:
            return

        # try to write directly
        err_code = self._do_write()
        if ErrorCode.is_error(err_code):
            self._connection_error(err_code)
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
            err_code = self._do_write()
            if ErrorCode.is_error(err_code):
                self._connection_error(err_code)
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
        # because of use level trigger, we write once
        try:
            chunk_size = self.sock.send(self.write_buffer)
        except IOError as e:
            chunk_size = 0
            err_code = utils.errno_from_ex(e)
            if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                err_code = ErrorCode.DO_AGAIN, 0
        else:
            if chunk_size == 0:
                err_code = ErrorCode.CLOSED
            else:
                err_code = ErrorCode.OK

        self.write_buffer = self.write_buffer[chunk_size:]
        return err_code

    def _on_read_event(self):
        """

        :return:
        """
        if self.state == ConnectionState.CONNECTING:
            self._handle_connect()

        if self.state != ConnectionState.CONNECTED:
            return

        err_code = self._do_read()
        if ErrorCode.is_error(err_code):
            self._connection_error(err_code)

    def _do_read(self):
        """

        :return:
        """
        # because of use level trigger, we read once
        try:
            data = self.sock.recv(READ_SIZE)
        except IOError as e:
            data = b""
            err_code = utils.errno_from_ex(e)
            if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                err_code = ErrorCode.DO_AGAIN
        else:
            if not data:
                err_code = ErrorCode.CLOSED
            else:
                err_code = ErrorCode.OK

        if data:
            self.protocol.data_received(data)

        return err_code

    def _handle_connect(self):
        """

        :return:
        """
        err_code = sock_helper.get_sock_error(self.sock)
        if err_code != 0:
            self._connection_failed(err_code)
            return

        self.channel.disable_writing()
        self.connection_established()

    def close(self, so_linger=False, delay=2):
        """

        :param so_linger: like socket so-linger option
        :param delay: sec
        :return:
        """
        if so_linger:
            assert delay > 0

        if self.ev.is_in_loop_thread():
            self._close_in_loop(so_linger, delay)
        else:
            self.ev.call_soon(self._close_in_loop, so_linger, delay)

    def _close_in_loop(self, so_linger: bool, delay: int):
        """
        if `write_buffer` is empty, close connection directly.
        else, if `so_linger` is false, close connection until write buffer
        is empty or error happened; otherwise, delay close connection
        after `delay` second and drop write buffer if it has, then close connection.
        :param so_linger:
        :param delay: sec
        :return:
        """
        if not self.write_buffer:
            self._close_connection()
            return

        if not so_linger:
            self.close_after_write = True
            return

        logger.warning(f"write buffer is not empty, close connection after {delay} sec")
        self.linger_timer = self.ev.call_later(delay, self._close_connection)

    def _close_connection(self):
        """

        :return:
        """
        if self._connection_will_be_closed():
            return

        self.state = ConnectionState.DISCONNECTING

        if self.linger_timer:
            self.linger_timer.cancel()

        self.write_buffer = b""
        self.channel.disable_all()

        # close on next loop
        self.ev.call_soon(self._close_force)

        self._connection_closed()

    def _connection_will_be_closed(self):
        """

        :return:
        """
        return self.state == ConnectionState.DISCONNECTING or self.state == ConnectionState.DISCONNECTED

    def _close_force(self):
        """

        :return:
        """
        self.state = ConnectionState.DISCONNECTED
        self.channel.close()

        del self.channel
        del self.sock
        del self.protocol
        del self.ctx
        del self.linger_timer
