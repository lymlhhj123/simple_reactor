# coding: utf-8

import libreactor
from libreactor import log
from libreactor.http import AsyncClient

logger = log.get_logger()
log.logger_init(logger)


loop = libreactor.get_event_loop()


async def fetch_url():
    async_client = AsyncClient(loop=loop)
    try:
        # https://www.jianshu.com/p/e23a1e917d19
        resp = await async_client.get("https://www.baidu.com/")
    except Exception as e:
        logger.exception(e)
    else:
        print(resp.status_code)
        print(resp.headers)
        # print(resp.text())


loop.run_coroutine_func(fetch_url)
loop.loop_forever()
