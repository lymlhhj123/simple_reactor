# coding: utf-8

from .const import ConnectType
from .connection import Connection


class Connector(object):

    def __init__(self, endpoint, context, connect_type, timeout=10, auto_reconnect=False):
        """

        :param endpoint:
        :param context:
        :param connect_type:
        :param timeout:
        :param auto_reconnect:
        """
        self._context = context
        self._event_loop = context.get_event_loop()
        self._endpoint = endpoint
        self._connect_type = connect_type
        self._timeout = timeout
        self._auto_reconnect = auto_reconnect

    def _on_connection_failed(self):
        """
        called when establish connection failed or timeout
        :return:
        """
        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def _on_connection_done(self):
        """
        called when connection closed by peer
        :return:
        """
        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def _on_connection_lost(self):
        """
        called when connection lost
        :return:
        """
        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def start_connect(self):
        """

        :return:
        """
        self._event_loop.call_soon(self._connect_in_loop)

    def _connect_in_loop(self):
        """

        :return:
        """
        conn = self._make_connection(self._endpoint, self._context, self._event_loop)
        if not conn:
            self._context.logger().error(f"failed to open connection to {self._endpoint}")
            return

        self._event_loop.call_soon(
            conn.start_connect, self._on_connection_done,
            self._on_connection_lost, self._on_connection_failed, self._timeout)

    def _make_connection(self, endpoint, context, event_loop):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :return:
        """
        if self._connect_type == ConnectType.TCP:
            return Connection.try_open_tcp(endpoint, context, event_loop)
        else:
            return Connection.try_open_unix(endpoint, context, event_loop)


class TcpConnector(Connector):
    
    def __init__(self, endpoint, context, timeout=10, auto_reconnect=False):
        """
        
        :param endpoint: 
        :param context: 
        :param timeout: 
        :param auto_reconnect: 
        """
        super(TcpConnector, self).__init__(endpoint, context, ConnectType.TCP, timeout, auto_reconnect)


class UnixConnector(Connector):

    def __init__(self, endpoint, context, timeout=10, auto_reconnect=False):
        """

        :param endpoint:
        :param context:
        :param timeout:
        :param auto_reconnect:
        """
        super(UnixConnector, self).__init__(endpoint, context, ConnectType.UNIX, timeout, auto_reconnect)
