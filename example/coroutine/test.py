# coding: utf-8

import simple_reactor


loop = simple_reactor.get_event_loop()


def test_gen():

    yield
    return 5


@simple_reactor.coroutine
def coro():
    # return generator directly
    return test_gen()


@simple_reactor.coroutine
def func():

    fut = loop.create_future()
    loop.call_later(4, simple_reactor.future_set_result, fut, None)
    yield fut

    return "data"


async def main():

    res = await coro()
    print(res)

    res = await func()
    print(res)


loop.create_task(main())

loop.run_forever()
