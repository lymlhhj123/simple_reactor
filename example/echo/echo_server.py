# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpServer
from libreactor.protocol import Protocol
from libreactor.options import Options
from libreactor.logging import get_logger, logger_init

logger = get_logger()
logger_init(logger)


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.connection.write(data)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop.current()

options = Options()
options.tcp_no_delay = True
options.close_on_exec = True
options.tcp_keepalive = True

server = TcpServer(9527, ev, MyContext(), options)
server.start()

ev.loop()
