# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpServer
from libreactor.options import Options
from libreactor.basic_protocols import LineReceiver
from libreactor.logging import get_logger, logger_init

logger = get_logger()
logger_init(logger)


class MyProtocol(LineReceiver):

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
        logger.info(f"line received: {line}")
        self.send_line(line)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop.current()

server = TcpServer(9527, ev, MyContext(), Options())
server.start()

ev.loop()
