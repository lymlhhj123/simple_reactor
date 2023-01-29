# coding: utf-8

from libreactor import Context
from libreactor import StreamReceiver
from libreactor import EventLoop
from libreactor import TcpClient


class MyProtocol(StreamReceiver):

    def __init__(self):

        super(MyProtocol, self).__init__()
        self.ops = 0
        self._end = False

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        if self._end:
            self.close_connection()
            return

        self.ops += 1
        self.send_msg(msg)

    def start_test(self):
        """

        :return:
        """
        start_time = self.event_loop.time()

        self.event_loop.call_later(60, self._count_down, start_time)

    def _count_down(self, start_time):
        """

        :param start_time:
        :return:
        """
        end_time = self.event_loop.time()
        self._end = True
        ops = self.ops / (end_time - start_time)
        print(f"ops: {ops}")


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.start_test()

    protocol.send_msg(b"hello")


ev = EventLoop()

ctx = MyContext(on_established=on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
