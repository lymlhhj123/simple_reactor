# coding: utf-8

from libreactor import log
from libreactor import get_event_loop
from libreactor.protocols import DatagramReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(DatagramReceiver):

    def connection_prepared(self):

        self.loop.run_coroutine_func(self.echo)

    async def echo(self):

        while True:
            datagram, addr = await self.read()
            self.send(datagram, addr)


loop = get_event_loop()
coro = loop.listen_udp(9527, MyProtocol)
loop.create_task(coro)

loop.loop_forever()
