# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpClient
from libreactor.protocol import Protocol


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
        self.connection.write(data)

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

        self._timer = self.event_loop.call_every(60, self._count_down)

    def _count_down(self):
        """

        :return:
        """
        now = self.event_loop.time()
        start_time, self.start_time = self.start_time, now
        io_count, self.io_count = self.io_count, 0
        ops = io_count / (now - start_time)
        print(f"ops: {ops}")

    def send_data(self):
        """

        :return:
        """
        self.connection.write(b"hello")


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.start_test()

    protocol.send_data()


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
