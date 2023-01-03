# coding: utf-8


class Connector(object):

    def __init__(self, endpoint, context, timeout=10, auto_reconnect=False):
        """

        :param endpoint:
        :param context:
        :param timeout:
        :param auto_reconnect:
        """
        self._context = context
        self._event_loop = context.get_event_loop()
        self._endpoint = endpoint
        self._timeout = timeout
        self._auto_reconnect = auto_reconnect

        self._connection_failed_cb = None
        self._connection_established_cb = None
        self._connection_lost_cb = None
        self._connection_done_cb = None

    def set_on_connection_failed(self, callback):
        """

        must be called before start_connect()
        :param callback:
        :return:
        """
        self._connection_failed_cb = callback

    def set_on_connection_established(self, callback):
        """

        must be called before start_connect()
        :param callback:
        :return:
        """
        self._connection_established_cb = callback

    def set_on_connection_lost(self, callback):
        """

        :param callback:
        :return:
        """
        self._connection_lost_cb = callback

    def set_on_connection_done(self, callback):
        """

        :param callback:
        :return:
        """
        self._connection_done_cb = callback

    def _on_connection_failed(self):
        """
        called when establish connection failed or timeout
        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        if self._connection_failed_cb:
            self._connection_failed_cb()

        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def _on_connection_done(self):
        """

        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        if self._connection_done_cb:
            self._connection_done_cb()

        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def _on_connection_lost(self):
        """

        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        if self._connection_lost_cb:
            self._connection_lost_cb()

        if self._auto_reconnect:
            self._event_loop.call_later(3, self._connect_in_loop)

    def _on_connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        assert self._event_loop.is_in_loop_thread()

        if self._connection_established_cb:
            self._connection_established_cb(protocol)

    def start_connect(self):
        """

        :return:
        """
        self._event_loop.call_soon(self._connect_in_loop)

    def _connect_in_loop(self):
        """

        :return:
        """
        conn = self._make_connection(self._endpoint, self._context, self._event_loop, self._timeout)
        if not conn:
            self._context.logger().error(f"failed to open connection to {self._endpoint}")
            return

        self._set_callback(conn)

    def _make_connection(self, endpoint, context, event_loop, timeout):
        """

        :param endpoint:
        :param context:
        :param event_loop:
        :param timeout:
        :return:
        """
        raise NotImplementedError

    def _set_callback(self, conn):
        """

        :param conn:
        :return:
        """
        conn.set_on_connection_done(self._on_connection_done)
        conn.set_on_connection_lost(self._on_connection_lost)
        conn.set_on_connection_failed(self._on_connection_failed)
        conn.set_on_connection_established(self._on_connection_established)
