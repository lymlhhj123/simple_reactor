# coding: utf-8

from libreactor import Context
from libreactor import Protocol
from libreactor import EventLoop
from libreactor import TcpClient


class MyProtocol(Protocol):

    def __init__(self):

        super(MyProtocol, self).__init__()
        self.io_count = 0
        self.start_time = 0
        self._timer = None

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.io_count += 1
        self.send_data(data)

    def connection_error(self, error):
        """

        :param error:
        :return:
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def start_test(self):
        """

        :return:
        """
        self.start_time = self.event_loop.time()

        self._timer = self.event_loop.call_later(60, self._count_down)

    def _count_down(self):
        """

        :return:
        """
        now = self.event_loop.time()
        start_time, self.start_time = self.start_time, now
        io_count, self.io_count = self.io_count, 0
        ops = io_count / (now - start_time)
        print(f"ops: {ops}")


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.start_test()

    protocol.send_data(b"hello")


ev = EventLoop()

ctx = MyContext(on_established=on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
