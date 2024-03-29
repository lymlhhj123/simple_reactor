# coding: utf-8

from simple_reactor import log
from simple_reactor import get_event_loop
from simple_reactor.protocols import IOStream

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(IOStream):

    async def start_echo(self):

        while True:
            try:
                await self.writeline("hello, world")
                line = await self.read_until_eof()
            except Exception as e:
                logger.exception(e)
                break

            line = line.decode("utf-8")
            logger.info("line received: %s", line)
            await self.loop.sleep(1)

        self.close()


loop = get_event_loop()


async def tcp_client():
    protocol = await loop.connect_tcp("127.0.0.1", 9527, MyProtocol)
    await protocol.start_echo()


loop.run_coroutine_func(tcp_client)

loop.run_forever()
