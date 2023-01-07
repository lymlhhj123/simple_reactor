# coding: utf-8

from libreactor import ClientContext
from libreactor import MessageReceiver
from libreactor import EventLoop


class MyProtocol(MessageReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.ctx.logger().info(f"{msg} received")


class MyContext(ClientContext):

    stream_protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.send_msg(b"hello")


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)
ctx.connect_tcp(("127.0.0.1", 9527), ev)

ev.loop()
