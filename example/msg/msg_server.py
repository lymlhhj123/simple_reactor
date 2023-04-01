# coding: utf-8

from libreactor import ServerContext
from libreactor import EventLoop
from libreactor import TcpServer
from libreactor import Options
from libreactor import MessageReceiver


class MyProtocol(MessageReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.send_msg(msg)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop.current()

server = TcpServer(9527, ev, MyContext(), Options())
server.start()

ev.loop()
