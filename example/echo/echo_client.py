# coding: utf-8

import libreactor
from libreactor import log
from libreactor import get_event_loop
from libreactor.protocols import StreamReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(StreamReceiver):

    async def start_echo(self):
        """

        :return:
        """
        while True:
            await self.write_line("hello, world")
            line = await self.read_line()
            print("line received:", line)

            await libreactor.sleep(1)


loop = get_event_loop()


async def tcp_client():
    protocol = await loop.connect_tcp("127.0.0.1", 9527, MyProtocol)
    await protocol.start_echo()


loop.run_coroutine_func(tcp_client)

loop.run_forever()
