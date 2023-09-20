# coding: utf-8

from libreactor import EventLoop
from libreactor import coroutine
from libreactor import Future, future_set_result


ev = EventLoop.current()


def net_io(delay):
    """just like network io"""

    f = Future()

    ev.call_later(delay, future_set_result, f, "data")

    return f


@coroutine
def coro1():

    a = yield 1
    print(a)

    yield ev.sleep(0.9)

    b = yield net_io(2)
    print("coro1", b)


@coroutine
def coro2():

    a = yield 5
    print(a)

    b = yield net_io(3)
    print("coro2", b)


@coroutine
def coro3():

    a = yield "a"
    print(a)

    b = yield net_io(2.4)
    print("coro3", b)

    return b


@coroutine
def co4():

    response = yield coro3()
    print("co4:", response)


coro1()
coro2()
coro3()
co4()

ev.loop()
