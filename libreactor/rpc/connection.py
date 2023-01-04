# coding: utf-8

import os
import socket
import errno

from libreactor.io_stream import IOStream
from libreactor import sock_util
from libreactor import fd_util
from libreactor import utils
from .const import State
from libreactor.rpc.status import Status

READ_SIZE = 8192


class Connection(IOStream):
    """
    stream tcp/unix connection, not thread safe, only used in event loop thread
    """

    def __init__(self, endpoint, sock, event_loop, context):
        """

        :param endpoint:
        :param sock:
        :param event_loop:
        :param context:
        """
        super(Connection, self).__init__(sock.fileno(), event_loop)

        fd_util.make_fd_async(sock.fileno())
        fd_util.close_on_exec(sock.fileno())

        self._endpoint = endpoint
        self._sock = sock
        self._state = State.DISCONNECTED

        self._write_buffer = b""

        self._context = context
        self._conn_id = -1
        self._protocol = None

        self._close_after_write = False
        self._linger_timer = None

        # client connect timer
        self._timeout_timer = None

        # callback
        self._on_connection_failed = None
        self._on_connection_established = None
        self._on_connection_lost = None
        self._on_connection_done = None

    @classmethod
    def try_open_tcp(cls, endpoint, context, event_loop):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :return:
        """
        host, port = endpoint
        try:
            addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except Exception as e:
            context.logger().error(f"failed to dns resolve {endpoint}, {e}")
            return

        if not addr_list:
            context.logger().error(f"dns resolve {endpoint} is empty")
            return

        for af, _, _, _, sa in addr_list:
            sock = socket.socket(family=af, type=socket.SOCK_STREAM)
            sock_util.set_tcp_no_delay(sock)
            sock_util.set_tcp_keepalive(sock)
            return cls(sa, sock, event_loop, context)

    @classmethod
    def try_open_unix(cls, endpoint, context, event_loop):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :return:
        """
        sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM)
        return cls(endpoint, sock, event_loop, context)

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
                self._context.logger().error(f"failed to try connect {self._endpoint}: {e}")
                return
        else:
            state = State.CONNECTED

        if state == State.CONNECTING:
            self._state = state
            self.enable_writing()
            self._timeout_timer = self._event_loop.call_later(timeout, self.connection_timeout)
        else:
            self.connection_established()

    def set_on_connection_done(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_done = callback

    def set_on_connection_lost(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_lost = callback

    def set_on_connection_failed(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_failed = callback

    def set_on_connection_established(self, callback):
        """

        :param callback:
        :return:
        """
        self._on_connection_established = callback

    @classmethod
    def from_sock(cls, sock, event_loop, context):
        """

        from server side connection
        :param sock:
        :param event_loop:
        :param context:
        :return:
        """
        endpoint = sock_util.get_remote_addr(sock)
        conn = cls(endpoint, sock, event_loop, context)
        return conn

    def connection_established(self):
        """

        :return:
        """
        self._context.logger().info(f"connection established to {self._endpoint}, fd: {self._fd}")
        self._state = State.CONNECTED

        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        self.enable_reading()

        conn_id = self._context.next_conn_id()
        self._conn_id = conn_id
        self._context.add_connection(conn_id, self)

        protocol = self._context.build_stream_protocol()
        self._protocol = protocol

        protocol.connection_established(self, self._event_loop, self._context)

        if self._on_connection_established:
            self._on_connection_established(protocol)

    def connection_made(self):
        """

        :return:
        """
        self._state = State.CONNECTED
        self.enable_reading()

        conn_id = self._context.next_conn_id()
        self._conn_id = conn_id
        self._context.add_connection(conn_id, self)

        protocol = self._context.build_stream_protocol()
        self._protocol = protocol

        protocol.connection_made(self, self._event_loop, self._context)

    def connection_timeout(self):
        """
        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._context.logger().error(f"timeout to connect {self._endpoint}")

        self._timeout_timer = None

        self._on_close()

        if self._on_connection_failed:
            self._on_connection_failed()

    def connection_failed(self):
        """

        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._timeout_timer.cancel()
        self._timeout_timer = None

        self._on_close()

        if self._on_connection_failed:
            self._on_connection_failed()

    def connection_lost(self):
        """

        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._on_close()
        self._protocol.connection_lost()

        if self._on_connection_lost:
            self._on_connection_lost()

    def connection_done(self):
        """

        Generally used in client side connection, trigger reconnect
        :return:
        """
        self._on_close()
        self._protocol.connection_done()

        if self._on_connection_done:
            self._on_connection_done()

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
            self._context.logger().error("connection is already closed, stop write")
            return

        if self._state == State.DISCONNECTING:
            self._context.logger().error("connection will be closed, stop write")
            return

        # already call close() method, dont accept data
        if self._close_after_write is True:
            self._context.logger().error("close() method is already called, stop write")
            return

        self._write_buffer += bytes_

        # may be still in connecting
        if self._state == State.CONNECTING:
            return

        # try to write directly
        status = self._do_write()
        if status != Status.OK:
            self._handle_read_write_error(status)
            return

        if self._write_buffer and not self.writable():
            self.enable_writing()

    def on_write(self):
        """

        :return:
        """
        if self._state == State.DISCONNECTING:
            self._context.logger().warning("connection will be closed, ignore write event")
            return

        # handle connecting and return directly
        if self._state == State.CONNECTING:
            self._handle_connect()
            return

        if self._write_buffer:
            status = self._do_write()
            if status != Status.OK:
                self._handle_read_write_error(status)
                return

        if self._write_buffer:
            return

        if self._close_after_write is True:
            self._context.logger().warning("write buffer is empty, close connection")
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
            self._context.logger().error(f"failed to connect {self._endpoint}: {reason}")
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
            if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
                return Status.OK
            elif err_code == errno.EPIPE:
                self._context.logger().error("broken pipe on write event")
                return Status.BROKEN_PIPE
            else:
                self._context.logger().error(f"error happened on write event, {e}")
                return Status.LOST

        if write_size == 0:
            return Status.CLOSED

        self._write_buffer = self._write_buffer[write_size:]
        return Status.OK

    def on_read(self):
        """

        :return:
        """
        if self._state == State.DISCONNECTING:
            self._context.logger().warning("connection will be closed, ignore read event")
            return

        status = self._do_read()
        if status != Status.OK:
            self._handle_read_write_error(status)

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
                    self._context.logger().error("broken pipe on read event")
                    return Status.BROKEN_PIPE
                else:
                    self._context.logger().error(f"error happened on read event, {e}")
                    return Status.LOST

            if not data:
                return Status.CLOSED

            self._data_received(data)

    def _data_received(self, data):
        """

        :param data:
        :return:
        """
        self._protocol.data_received(data)

    def _handle_read_write_error(self, status):
        """

        handle error when read or write
        :param status:
        :return:
        """
        if status == Status.CLOSED:
            self.connection_done()
        elif status == Status.BROKEN_PIPE:
            self.connection_done()
        else:
            self.connection_lost()
    
    def close(self, so_linger=False, delay=10):
        """

        :param so_linger:
        :param delay: sec
        :return:
        """
        if not self._write_buffer:
            self._on_close()
            return

        self._context.logger().warning("write buffer is not empty, delay to close connection")

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
            self._context.logger().warning("write buffer is not empty, drop it and close connection")

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

        self._context.remove_connection(self._conn_id)
        self._conn_id = -1
        self._protocol = None
