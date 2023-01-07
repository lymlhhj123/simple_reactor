# coding: utf-8

from libreactor import ServerContext
from libreactor import StreamReceiver
from libreactor import EventLoop


class MyProtocol(StreamReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.send_msg(msg)


class MyContext(ServerContext):

    stream_protocol_cls = MyProtocol


ev = EventLoop()

ctx = MyContext()
ctx.listen_tcp(9527, ev)

ev.loop()
