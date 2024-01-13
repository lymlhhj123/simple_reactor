# coding: utf-8

from simple_reactor import log
from simple_reactor import get_event_loop
from simple_reactor.protocols import IOStream

logger = log.get_logger()
log.logger_init(logger)


class MyProtocol(IOStream):
    
    def __init__(self):
        
        super().__init__()

        self.io_count = 0

    async def start_echo(self):
        """

        :return:
        """
        self.loop.call_later(60, self.perf_count)

        while True:
            await self.write_line("hello, world")
            await self.read_line()

            self.io_count += 1

    def perf_count(self):

        logger.info(f"ops: {self.io_count // 60}")
        self.io_count = 0
        self.loop.call_later(60, self.perf_count)


loop = get_event_loop()


async def unix_client():

    protocol = await loop.connect_unix("/var/run/my_unix.sock", MyProtocol)

    loop.run_coroutine_func(protocol.start_echo)


loop.run_coroutine_func(unix_client)

loop.run_forever()
