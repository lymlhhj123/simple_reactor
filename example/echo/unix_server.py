# coding: utf-8

from simple_reactor import log
from simple_reactor import get_event_loop
from simple_reactor.protocols import IOStream

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(IOStream):

    def connection_made(self):

        self.loop.run_coroutine_func(self.echo)

    async def echo(self):

        while True:
            data = await self.read_line()
            await self.write_line(b"ok, data received: " + data)


loop = get_event_loop()
coro = loop.listen_unix("/var/run/my_unix.sock", MyProtocol)
loop.create_task(coro)

loop.loop_forever()
