# coding: utf-8

import os
import socket
import errno

from libreactor.io_stream import IOStream
from libreactor import sock_util
from libreactor import fd_util
from libreactor import utils
from libreactor.rpc.tcp.const import State
from libreactor.rpc.tcp.status import Status

READ_SIZE = 8192


class Connection(IOStream):

    def __init__(self, endpoint, sock, ctx, event_loop):
        """

        :param endpoint:
        :param sock:
        :param ctx:
        :param event_loop:
        """
        super(Connection, self).__init__(sock.fileno(), event_loop)

        fd_util.make_fd_async(sock.fileno())
        fd_util.close_on_exec(sock.fileno())

        self._endpoint = endpoint
        self._sock = sock
        self._state = State.DISCONNECTED

        self._write_buffer = b""

        self._ctx = ctx
        self._conn_id = -1
        self._protocol = None

        self._close_after_write = False
        self._linger_timer = None

        # client connect timer
        self._timeout_timer = None

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

    def start_connect(self, timeout=10):
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
                state = State.CONNECTED
            elif err_code in [errno.EINPROGRESS, errno.EALREADY]:
                state = State.CONNECTING
            else:
                self._ctx.logger().error(f"failed to try connect {self._endpoint}: {e}")
                self._ctx.on_connection_failed(err_code)
                return
        else:
            state = State.CONNECTED

        if state == State.CONNECTING:
            self._state = state
            self.enable_writing()
            self._timeout_timer = self._event_loop.call_later(timeout, self.connection_timeout)
        else:
            self.connection_established()

    def connection_established(self):
        """

        :return:
        """
        self._ctx.logger().info(f"connection established to {self._endpoint}, fd: {self._fd}")
        self._state = State.CONNECTED

        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        self.enable_reading()

        conn_id = self._ctx.add_connection(self)
        self._conn_id = conn_id

        protocol = self._ctx.build_protocol()
        protocol.set_ctx(self._ctx)
        protocol.set_connection(self)
        protocol.set_event_loop(self._event_loop)

        protocol.connection_established(self, self._event_loop)

        self._ctx.on_connection_established(protocol)

    def connection_made(self):
        """

        :return:
        """
        self._state = State.CONNECTED
        self.enable_reading()

        conn_id = self._ctx.add_connection(self)
        self._conn_id = conn_id

        protocol = self._ctx.build_protocol()
        protocol.set_ctx(self._ctx)
        protocol.set_connection(self)
        protocol.set_event_loop(self._event_loop)

        self._protocol = protocol
        protocol.connection_made(self, self._event_loop)

        self._ctx.on_connection_made(protocol)

    def connection_timeout(self):
        """
        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._ctx.logger().error(f"timeout to connect {self._endpoint}")

        self._timeout_timer = None

        self._on_close()

        self._ctx.on_connection_timeout()

    def connection_failed(self, err_code):
        """

        Generally used in client side connection, trigger reconnect
        :param err_code:
        :return:
        """
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        self._on_close()

        self._ctx.on_connection_failed(err_code)

    def connection_lost(self, err_code):
        """

        Generally used in client side connection, trigger reconnect
        :param err_code:
        :return:
        """
        self._on_close()
        self._protocol.connection_lost()

        self._ctx.on_connection_lost(err_code)

    def connection_done(self):
        """

        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._on_close()
        self._protocol.connection_done()

        self._ctx.on_connection_done()

    def write(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        self._write(bytes_)

    def _write(self, bytes_):
        """

        :param bytes_:
        :return:
        """
        if self._state == State.DISCONNECTED:
            self._ctx.logger().error("connection is already closed, stop write")
            return

        if self._state == State.DISCONNECTING:
            self._ctx.logger().error("connection will be closed, stop write")
            return

        # already call close() method, dont accept data
        if self._close_after_write is True:
            self._ctx.logger().error("close() method is already called, stop write")
            return

        self._write_buffer += bytes_

        # may be still in connecting
        if self._state == State.CONNECTING:
            return

        # try to write directly
        status = self._do_write()
        if status != Status.OK:
            return

        if self._write_buffer and not self.writable():
            self.enable_writing()

    def on_write(self):
        """

        :return:
        """
        if self._state == State.DISCONNECTING:
            self._ctx.logger().warning("connection will be closed, ignore write event")
            return

        # handle connecting and return directly
        if self._state == State.CONNECTING:
            self._handle_connect()
            return

        if self._write_buffer:
            status = self._do_write()
            if status != Status.OK:
                return

        if self._write_buffer:
            return

        if self._close_after_write is True:
            self._ctx.logger().warning("write buffer is empty, close connection")
            self._on_close()
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
            self._ctx.logger().error(f"failed to connect {self._endpoint}: {reason}")
            self.connection_failed(err_code)
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
            if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                return Status.OK
            elif err_code == errno.EPIPE:
                self._ctx.logger().error("broken pipe on write event")
                self.connection_done()
                return Status.BROKEN_PIPE
            else:
                self._ctx.logger().error(f"error happened on write event, {e}")
                self.connection_lost(err_code)
                return Status.LOST

        if write_size == 0:
            self.connection_done()
            return Status.CLOSED

        self._write_buffer = self._write_buffer[write_size:]
        return Status.OK

    def on_read(self):
        """

        :return:
        """
        if self._state == State.DISCONNECTING:
            self._ctx.logger().warning("connection will be closed, ignore read event")
            return

        self._do_read()

    def _do_read(self):
        """

        :return:
        """
        while True:
            try:
                data = self._sock.recv(READ_SIZE)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                    return Status.OK
                elif err_code == errno.EPIPE:
                    self._ctx.logger().error("broken pipe on read event")
                    self.connection_done()
                    return Status.BROKEN_PIPE
                else:
                    self._ctx.logger().error(f"error happened on read event, {e}")
                    self.connection_lost(err_code)
                    return Status.LOST

            if not data:
                self.connection_done()
                return Status.CLOSED

            self._data_received(data)

    def _data_received(self, data):
        """

        :param data:
        :return:
        """
        self._protocol.data_received(data)

    def close(self, so_linger=False, delay=10):
        """

        :param so_linger:
        :param delay: sec
        :return:
        """
        if not self._write_buffer:
            self._on_close()
            return

        self._ctx.logger().warning("write buffer is not empty, delay to close connection")

        # wait write buffer empty;
        # if not set `so_linger`, close connection until write buffer is empty or error happened;
        # otherwise, delay close connection after `delay` second and drop write buffer if it has.
        self._close_after_write = True
        if not so_linger:
            return

        assert delay >= 0
        self._linger_timer = self._event_loop.call_later(delay, self._delay_close)

    def _delay_close(self):
        """

        :return:
        """
        if self._write_buffer:
            self._ctx.logger().warning("write buffer is not empty, drop it and close connection")

        self._on_close()

    def _on_close(self):
        """

        :return:
        """
        if self._state == State.DISCONNECTING or self._state == State.DISCONNECTED:
            return

        self._state = State.DISCONNECTING

        if self._linger_timer:
            self._linger_timer.cancel()
            self._linger_timer = None

        self._write_buffer = b""
        self.disable_all()

        # close on next loop
        self._event_loop.call_soon(self._close_force)

    def _close_force(self):
        """

        :return:
        """
        self._event_loop.remove_io_stream(self)

        self.close_fd()

        self._state = State.DISCONNECTED
        self._sock = None

        self._ctx.remove_connection(self._conn_id)
        self._conn_id = -1
        self._protocol = None
        self._ctx = None
