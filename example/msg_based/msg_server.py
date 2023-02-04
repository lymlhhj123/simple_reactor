# coding: utf-8

from libreactor import Context
from libreactor import StreamReceiver
from libreactor import EventLoop
from libreactor import TcpServer


class MyProtocol(StreamReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.send_msg(msg)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
