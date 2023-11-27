# coding: utf-8

import libreactor
from libreactor import log
from libreactor import get_event_loop
from libreactor.protocols import DatagramReceiver

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(DatagramReceiver):

    async def start_echo(self):

        while True:
            self.send("hello, world")
            datagram, addr = await self.read()
            print("data received:", datagram, addr)

            await libreactor.sleep(1)


loop = get_event_loop()


async def udp_client():
    protocol = await loop.connect_udp("127.0.0.1", 9527, MyProtocol)
    await protocol.start_echo()


loop.run_coroutine_func(udp_client)

loop.run_forever()
