# coding: utf-8

import libreactor
from libreactor.http import AsyncClient


loop = libreactor.get_event_loop()


async def fetch_url():
    async_client = AsyncClient(loop=loop)
    try:
        resp = await async_client.get("https://www.jianshu.com/p/e23a1e917d19")
    except Exception as e:
        print(e)
    else:
        print(resp.status_code)
        print(resp.headers)
        print(resp.text())


loop.run_coroutine_func(fetch_url)
loop.loop_forever()
