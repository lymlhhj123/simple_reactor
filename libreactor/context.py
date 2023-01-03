# coding: utf-8

from threading import Lock

from .event_loop import EventLoop
from .event_loop_thread import EventLoopThread
from . import stream_rpc
from . import _logger


class Context(object):

    def __init__(self, io_threads=1, stream_protocol_cls=None,
                 dgram_protocol_cls=None, logger=None, log_debug=False):
        """

        :param io_threads:
        :param stream_protocol_cls:
        :param dgram_protocol_cls:
        :param log_debug:
        """
        self._io_threads = io_threads
        self._stream_protocol_cls = stream_protocol_cls
        self._dgram_protocol_cls = dgram_protocol_cls

        self._logger = logger or _logger.get_logger(log_debug)

        # main event loop
        self._ev_list = [EventLoop()]

        self._lock = Lock()
        self._ev_id = 0
        self._conn_id = 0
        self._connection_map = {}

        self._init()

    def _init(self):
        """

        :return:
        """
        for _ in range(self._io_threads):
            ev_t = EventLoopThread()
            ev_t.start()
            ev = ev_t.get_event_loop()
            self._ev_list.append(ev)

        self._register_signal_handler()

    def _register_signal_handler(self):
        """

        :return:
        """

    def main_ev(self):
        """

        :return:
        """
        return self._ev_list[0]

    def main_loop(self):
        """

        :return:
        """
        self._ev_list[0].loop()

    def logger(self):
        """

        :return:
        """
        return self._logger

    def next_conn_id(self):
        """

        :return:
        """
        with self._lock:
            conn_id = self._conn_id
            self._conn_id += 1

        return conn_id

    def get_event_loop(self):
        """

        :return:
        """
        with self._lock:
            ev_id = self._ev_id
            self._ev_id += 1

        return self._ev_list[ev_id % len(self._ev_list)]

    def add_connection(self, conn_id, connection):
        """

        :param conn_id:
        :param connection:
        :return:
        """
        with self._lock:
            self._connection_map[conn_id] = connection

    def remove_connection(self, conn_id):
        """

        :param conn_id:
        :return:
        """
        with self._lock:
            self._connection_map.pop(conn_id, None)

    def listen_tcp(self, port):
        """

        :param port:
        :return:
        """
        tcp_server = stream_rpc.TcpServer(port, self)
        tcp_server.start()

    def connect_tcp(self, host, port, timeout=10, auto_reconnect=False,
                    on_connection_failed=None, on_connection_established=None):
        """

        :param host:
        :param port:
        :param timeout:
        :param auto_reconnect:
        :param on_connection_failed:
        :param on_connection_established:
        :return:
        """
        connector = stream_rpc.TcpConnector((host, port), self, timeout, auto_reconnect)
        connector.set_on_connection_failed(on_connection_failed)
        connector.set_on_connection_established(on_connection_established)
        connector.start_connect()

    def listen_stream_unix(self, unix_path):
        """

        :param unix_path:
        :return:
        """
        unix_server = stream_rpc.UnixServer(unix_path, self)
        unix_server.start()

    def connect_stream_unix(self, unix_file, timeout=10, auto_reconnect=False,
                            on_connection_failed=None, on_connection_established=None):
        """

        :param unix_file:
        :param timeout:
        :param auto_reconnect:
        :param on_connection_failed:
        :param on_connection_established:
        :return:
        """
        connector = stream_rpc.UnixConnector(unix_file, self, timeout, auto_reconnect)
        connector.set_on_connection_failed(on_connection_failed)
        connector.set_on_connection_established(on_connection_established)
        connector.start_connect()

    def listen_udp(self, port):
        """

        :param port:
        :return:
        """

    def connect_udp(self, host, port):
        """

        :param host:
        :param port:
        :return:
        """

    def build_stream_protocol(self):
        """

        :return:
        """
        return self._stream_protocol_cls()

    def build_dgram_protocol(self):
        """

        :return:
        """
        return self._dgram_protocol_cls()
