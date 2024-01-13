# coding: utf-8

import simple_reactor
from simple_reactor import log
from simple_reactor import get_event_loop
from simple_reactor.protocols import IODatagram

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(IODatagram):

    async def start_echo(self):

        while True:
            await self.send("hello, world")
            datagram, addr = await self.read()
            print("data received:", datagram, addr)

            await simple_reactor.sleep(1)


loop = get_event_loop()


async def udp_client():
    protocol = await loop.connect_udp("127.0.0.1", 9527, MyProtocol)
    await protocol.start_echo()


loop.run_coroutine_func(udp_client)

loop.run_forever()
