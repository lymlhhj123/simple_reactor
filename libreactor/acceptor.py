# coding: utf-8

from .connection import Connection
from .channel import Channel
from . import sock_helper
from . import fd_helper
from . import utils
from . import error
from . import log

logger = log.get_logger()


class Acceptor(object):

    def __init__(self, loop, sock, proto_factory, options):

        self.loop = loop
        self.sock = sock
        self.proto_factory = proto_factory
        self.options = options

        self.placeholder = open("/dev/null")
        self.channel = None

    def start(self):
        """

        :return:
        """
        assert self.loop.is_in_loop_thread()

        channel = Channel(self.sock.fileno(), self.loop)
        channel.set_read_callback(self._accept_new_connection)
        channel.enable_reading()

        self.channel = channel

    def _accept_new_connection(self):
        """

        :return:
        """
        while True:
            try:
                sock, addr = self.sock.accept()
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code in [error.EAGAIN, error.EWOULDBLOCK]:
                    break
                elif err_code == error.EMFILE:
                    self._too_many_open_file()
                else:
                    self._do_accept_error()
                    logger.error("unknown error happened on do accept: %s", e)
                    break
            else:
                self._on_new_connection(sock, addr)

    def _too_many_open_file(self):
        """

        :return:
        """
        logger.error("too many open file, accept and close connection")
        self.placeholder.close()
        sock, _ = self.sock.accept()
        sock.close()
        self._placeholder = open("/dev/null")

    def _do_accept_error(self):
        """

        :return:
        """
        self.channel.disable_reading()
        self.channel.close()
        self.sock.close()

        self.channel = None
        self.sock = None

        # self.loop.call_soon(self.start)

    def _on_new_connection(self, sock, addr):
        """

        :param sock:
        :param addr:
        :return:
        """
        logger.info(f"new connection from {addr}, fd: {sock.fileno()}")

        sock_helper.set_sock_async(sock)

        if self.options.tcp_no_delay:
            sock_helper.set_tcp_no_delay(sock)

        if self.options.tcp_keepalive:
            sock_helper.set_tcp_keepalive(sock)

        fd_helper.close_on_exec(sock.fileno(), self.options.close_on_exec)

        protocol = self.proto_factory()
        conn = Connection(sock, protocol, self.loop)
        self.loop.call_soon(conn.connection_made, addr)
