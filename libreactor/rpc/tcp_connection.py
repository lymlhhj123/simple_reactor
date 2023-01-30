# coding: utf-8

import os
import socket
import errno

from libreactor.io_stream import IOStream
from libreactor import sock_util
from libreactor import fd_util
from libreactor import utils
from libreactor.const import ConnectionState
from libreactor.const import ConnectionErr
from libreactor import logging

logger = logging.get_logger()

READ_SIZE = 8192


class TcpConnection(IOStream):

    def __init__(self, endpoint, sock, ctx, event_loop):
        """

        :param endpoint:
        :param sock:
        :param ctx:
        :param event_loop:
        """
        super(TcpConnection, self).__init__(sock.fileno(), event_loop)

        fd_util.make_fd_async(sock.fileno())
        fd_util.close_on_exec(sock.fileno())

        self._endpoint = endpoint
        self._sock = sock
        self._state = ConnectionState.DISCONNECTED

        self._write_buffer = b""

        self._ctx = ctx
        self._protocol = None

        self._close_after_write = False
        self._linger_timer = None

        # client connect timer
        self._timeout_timer = None

        self._closed_callback = None
        self._err_callback = None

    @classmethod
    def from_sock(cls, sock, ctx, event_loop):
        """

        from server side connection
        :param sock:
        :param ctx:
        :param event_loop:
        :return:
        """
        endpoint = sock_util.get_remote_addr(sock)
        conn = cls(endpoint, sock, ctx, event_loop)
        return conn

    def set_callback(self, closed_callback=None, err_callback=None):
        """

        :param closed_callback:
        :param err_callback:
        :return:
        """
        self._closed_callback = closed_callback
        self._err_callback = err_callback

    def try_open(self, timeout=10):
        """

        :param timeout:
        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        try:
            self._sock.connect(self._endpoint)
        except socket.error as e:
            err_code = e.errno
            if err_code == errno.EISCONN:
                state = ConnectionState.CONNECTED
            elif err_code == errno.EINPROGRESS or err_code == errno.EALREADY:
                state = ConnectionState.CONNECTING
            else:
                self._ctx.on_connection_failed(err_code)
                return
        else:
            state = ConnectionState.CONNECTED

        if state == ConnectionState.CONNECTING:
            self._state = state
            self.enable_writing()
            self._timeout_timer = self._event_loop.call_later(timeout, self.connection_timeout)
        else:
            self.connection_established()

    def connection_established(self):
        """

        client side connection
        :return:
        """
        logger.info(f"connection established to {self._endpoint}, fd: {self._fd}")
        self._state = ConnectionState.CONNECTED

        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        self.enable_reading()

        self._protocol = self._ctx.build_protocol()
        self._protocol.connection_established(self, self._event_loop, self._ctx)

    def connection_made(self):
        """

        server side connection
        :return:
        """
        self._state = ConnectionState.CONNECTED
        self.enable_reading()

        self._protocol = self._ctx.build_protocol()
        self._protocol.connection_made(self, self._event_loop, self._ctx)

    def connection_timeout(self):
        """

        client establish connection timeout
        :return:
        """
        logger.error(f"timeout to connect {self._endpoint}")
        self._timeout_timer = None
        self.connection_error(ConnectionErr.TIMEOUT)

    def connection_failed(self):
        """
        client failed to establish connection
        :return:
        """
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        self.connection_error(ConnectionErr.CONNECT_FAILED)

    def connection_error(self, error):
        """

        :param error:
        :return:
        """
        self._close_connection()

        if self._protocol:
            self._protocol.connection_error(error)

        if self._err_callback:
            self._err_callback(error)

    def write(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        if self._event_loop.is_in_loop_thread():
            self._write_impl(bytes_)
        else:
            self._event_loop.call_soon(self._write_impl, bytes_)

    def _write_impl(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        if self._state in [ConnectionState.DISCONNECTED, ConnectionState.DISCONNECTING]:
            return

        # already call close() method, don't write data
        if self._close_after_write is True:
            logger.error("close method is already called, cannot write")
            return

        self._write_buffer += bytes_

        # still in connecting
        if self._state == ConnectionState.CONNECTING:
            return

        # try to write directly
        error = self._do_write()
        if error != ConnectionErr.OK:
            self.connection_error(error)
            return

        if self._write_buffer and not self.writable():
            self.enable_writing()

    def on_write(self):
        """

        :return:
        """
        # handle connecting
        if self._state == ConnectionState.CONNECTING:
            self._handle_connect()

        if self._state != ConnectionState.CONNECTED:
            return

        if self._write_buffer:
            error = self._do_write()
            if error != ConnectionErr.OK:
                self.connection_error(error)
                return

        if self._write_buffer:
            return

        if self._close_after_write is True:
            self._close_connection()
            return

        if self.writable():
            self.disable_writing()

    def _handle_connect(self):
        """

        :return:
        """
        err_code = sock_util.get_sock_error(self._sock)
        if err_code != 0:
            reason = os.strerror(err_code)
            logger.error(f"failed to connect {self._endpoint}: {reason}")
            self.connection_failed()
            return

        self.disable_writing()
        self.connection_established()

    def _do_write(self):
        """

        :return:
        """
        try:
            write_size = self._sock.send(self._write_buffer)
        except Exception as e:
            err_code = utils.errno_from_ex(e)
            if err_code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return ConnectionErr.OK
            elif err_code == errno.EPIPE:
                return ConnectionErr.BROKEN_PIPE
            else:
                return ConnectionErr.UNKNOWN

        if write_size == 0:
            return ConnectionErr.PEER_CLOSED

        self._write_buffer = self._write_buffer[write_size:]
        return ConnectionErr.OK

    def on_read(self):
        """

        :return:
        """
        if self._state == ConnectionState.CONNECTING:
            self._handle_connect()

        if self._state != ConnectionState.CONNECTED:
            return

        error = self._do_read()
        if error != ConnectionErr.OK:
            self.connection_error(error)
            return

    def _do_read(self):
        """

        :return:
        """
        while True:
            try:
                data = self._sock.recv(READ_SIZE)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    return ConnectionErr.OK
                elif err_code == errno.EPIPE:
                    return ConnectionErr.BROKEN_PIPE
                else:
                    return ConnectionErr.UNKNOWN

            if not data:
                return ConnectionErr.PEER_CLOSED

            self._data_received(data)

    def _data_received(self, data):
        """

        :param data:
        :return:
        """
        self._protocol.data_received(data)

    def close(self, so_linger=False, delay=2):
        """

        :param so_linger: like socket so-linger option
        :param delay: sec
        :return:
        """
        assert delay > 0
        if self._event_loop.is_in_loop_thread():
            self._close_impl(so_linger, delay)
        else:
            self._event_loop.call_soon(self._close_impl, so_linger, delay)

    def _close_impl(self, so_linger, delay):
        """

        :param so_linger:
        :param delay: sec
        :return:
        """
        if not self._write_buffer:
            self._close_connection()
            return

        logger.warning("write buffer is not empty, delay to close connection")

        # wait write buffer empty. if not set `so_linger`, close connection until
        # write buffer is empty or error happened; otherwise, delay close connection
        # after `delay` second and drop write buffer if it has.
        self._close_after_write = True
        if not so_linger:
            return

        self._linger_timer = self._event_loop.call_later(delay, self._delay_close)

    def _delay_close(self):
        """

        :return:
        """
        if self._write_buffer:
            logger.warning("force close connection and drop write buffer")

        self._close_connection()

    def _close_connection(self):
        """

        :return:
        """
        if self._state in [ConnectionState.DISCONNECTING, ConnectionState.DISCONNECTED]:
            return

        self._state = ConnectionState.DISCONNECTING

        if self._linger_timer:
            self._linger_timer.cancel()
            self._linger_timer = None

        self._write_buffer = b""
        self.disable_all()

        if self._closed_callback:
            self._closed_callback(self)

        if self._err_callback:
            self._err_callback(ConnectionErr.USER_CLOSED)

        # maybe still handle events, close on next loop
        self._event_loop.call_soon(self._close_force)

    def _close_force(self):
        """

        :return:
        """
        self._event_loop.remove_io_stream(self)

        self.close_fd()

        self._state = ConnectionState.DISCONNECTED
        self._sock = None

        self._protocol = None
        self._ctx = None
