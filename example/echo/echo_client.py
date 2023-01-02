# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import Protocol

PING = b"PING"


class ClientProtocol(Protocol):

    def __init__(self):
        super(ClientProtocol, self).__init__()
        self.count = 0
        self.start_time = 0
        self._timer = None

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.count += 1
        self.send_data(PING)

    def count_down(self):
        """

        :return:
        """
        self.start_time = self.event_loop.time()
        self._timer = self.event_loop.call_later(60, self.end_count)

    def connection_lost(self):
        """

        :return:
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def connection_done(self):
        """

        :return:
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def end_count(self):
        """

        :return:
        """
        now = self.event_loop.time()
        self.context.logger().info(f"ops: {self.count / (now - self.start_time)}")
        self._timer = None
        self.close_connection()


context = Context(stream_protocol_cls=ClientProtocol, log_debug=True)


def succeed_callback(protocol):
    """
    
    :param protocol:
    :return: 
    """
    protocol.context.logger().info("start test")
    protocol.count_down()
    protocol.send_data(PING)


def tcp_main():
    """

    :return:
    """
    context.connect_tcp("127.0.0.1", 9527, on_connection_established=succeed_callback)

    context.main_loop()


def unix_main():
    """

    :return:
    """
    context.connect_unix("/var/run/echo.sock", on_connection_established=succeed_callback)

    context.main_loop()


tcp_main()
