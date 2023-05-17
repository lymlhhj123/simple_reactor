# coding: utf-8

import socket
import errno

from ..core import Channel
from ..common import logging
from ..common import const
from ..common import utils
from ..common import sock_helper


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
        self.state = const.ConnectionState.DISCONNECTED
        self.write_buffer = b""
        self.protocol = None

        self.error_code = const.ErrorCode.OK

        self.closing = False
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
        return const.ErrorCode.str_error(self.error_code)

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
            err_code = const.ErrorCode.OK

        if err_code == errno.EISCONN or err_code == const.ErrorCode.OK:
            self.connection_established()
        elif err_code == errno.EINPROGRESS or err_code == errno.EALREADY:
            self._wait_connection_established(timeout)
        else:
            self._connection_failed(err_code)

    def _wait_connection_established(self, timeout):
        """

        :return:
        """
        self.state = const.ConnectionState.CONNECTING
        self.channel.enable_writing()
        self.timeout_timer = self.ev.call_later(timeout, self._connection_timeout)

    def connection_established(self):
        """
        client side established connection
        :return:
        """
        if sock_helper.is_self_connect(self.sock):
            logger.warning("sock is self connect, force close")
            self._connection_lost()
            return

        logger.info(f"connection established to {self.endpoint}, fd: {self.sock.fileno()}")
        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        self.state = const.ConnectionState.CONNECTED
        self.channel.enable_reading()

        self.protocol = self._build_protocol()
        self.protocol.connection_established()
        self.ctx.connection_established(self.protocol)

    def connection_made(self, addr):
        """
        server side accept new connection
        :param addr:
        :return:
        """
        self.endpoint = addr

        self.state = const.ConnectionState.CONNECTED
        self.channel.enable_reading()

        self.protocol = self._build_protocol()
        self.protocol.connection_made()
        self.ctx.connection_made(self.protocol)

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
        self._connection_failed(const.ErrorCode.TIMEOUT)

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

        self._connection_lost()
        self.ctx.connection_failure(self)

    def _connection_error(self, err_code):
        """
        error happened when on read/write
        :return:
        """
        self.error_code = err_code

        self._connection_lost()

        self.protocol.connection_error()
        self.ctx.connection_error(self)

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
        if self.closing is True:
            return

        self.write_buffer += data

        # still in connecting
        if self.state == const.ConnectionState.CONNECTING:
            return

        # try to write directly
        err_code = self._do_write()
        if const.ErrorCode.is_error(err_code):
            self._connection_error(err_code)
            return

        if self.write_buffer and not self.channel.writable():
            self.channel.enable_writing()

    def _on_write_event(self):
        """

        :return:
        """
        if self.state == common.ConnectionState.CONNECTING:
            self._handle_connect()

        if self.state != common.ConnectionState.CONNECTED:
            return

        if self.write_buffer:
            err_code = self._do_write()
            if common.ErrorCode.is_error(err_code):
                self._connection_error(err_code)
                return

        if self.write_buffer:
            return

        if self.closing is True:
            self._close_impl()
            return

        if self.channel.writable():
            self.channel.disable_writing()

    def _do_write(self):
        """

        :return:
        """
        err_code, chunk_size = self.channel.write(self.write_buffer)
        self.write_buffer = self.write_buffer[chunk_size:]
        return err_code

    def _on_read_event(self):
        """

        :return:
        """
        if self.state == common.ConnectionState.CONNECTING:
            self._handle_connect()

        if self.state != common.ConnectionState.CONNECTED:
            return

        err_code = self._do_read()

        # todo:
        self._connection_lost()

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
        err_code = sock_helper.get_sock_error(self.sock)
        if err_code != 0:
            self._connection_failed(err_code)
            return

        self.channel.disable_writing()
        self.connection_established()

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
            self._connection_lost()
            return

    def abort(self):
        """

        :return:
        """
        assert self.ev.is_in_loop_thread()

    def _close_force(self):
        """

        :return:
        """
        if self.write_buffer:
            self.write_buffer = b""

        self.channel.disable_all()

        self._close_impl()

    def _close_impl(self):
        """

        :return:
        """
        if self.closing is True:
            return

        self.closing = True

        self.channel.disable_reading()

        # write buffer is empty, close it
        if not self.write_buffer:
            self._connection_lost()
            return

    def _connection_lost(self, reason):
        """

        :return:
        """
        self.channel.close()
        self.sock.close()

        del self.channel
        del self.sock
        del self.protocol
        del self.ctx

        self.ev.call_soon
