# coding: utf-8

from concurrent import futures as __futures

from ._loop_helper import get_event_loop

__Future = __futures.Future


def create_future():

    return __Future()


def is_future(f):
    """return ture if f is future"""

    return isinstance(f, __Future)


def maybe_future(fut):
    """wrap fut to future"""
    if is_future(fut):
        return fut

    proxy = create_future()
    future_set_result(proxy, fut)
    return proxy


def with_timeout(fut, timeout):
    """wait future finished or timeout"""

    def _fut_timeout():

        if future_is_done(fut):
            return

        fut.set_exception(TimeoutError("future timeout"))

    loop = get_event_loop()
    handle = loop.call_later(timeout, _fut_timeout)
    future_add_done_callback(fut, lambda _: handle.cancel())
    return fut


def chain_future(fut_in, fut_out):

    def copy_result(f):

        assert f is fut_in

        if future_is_done(fut_out):
            return

        if future_get_exception(f):
            future_set_exception(fut_out, future_get_exception(f))
        else:
            future_set_result(fut_out, future_get_result(f))

    future_add_done_callback(fut_in, copy_result)
    return fut_out


def multi_future(fs):

    final_future = create_future()

    waiting_finished = set(fs)

    if not fs:
        future_set_result(final_future, [])

    def callback(fut):

        waiting_finished.discard(fut)
        if waiting_finished:
            return

        result_list = []
        for f in fs:
            try:
                result = future_get_result(f)
            except Exception as e:
                if not future_is_done(final_future):
                    future_set_exception(final_future, e)
                    break
            else:
                result_list.append(result)

        if not final_future.done():
            future_set_result(final_future, result_list)

    children = set()
    for child in fs:
        if child in children:
            continue

        children.add(child)
        future_add_done_callback(child, callback)

    return final_future


# future helper function

def future_is_done(fut):
    """return true if future is done"""

    return fut.done()


def future_add_done_callback(fut, callback):
    """add callback to future, auto called when future is done"""

    def _fn(f):

        loop = get_event_loop()
        loop.call_soon(callback, f)

    fut.add_done_callback(_fn)


def future_get_result(fut):
    """get result from future"""

    return fut.result()


def future_set_result(fut, value):
    """set result to future"""

    if future_is_done(fut):
        return

    fut.set_result(value)


def future_get_exception(fut):
    """get exception from future"""

    return fut.exception()


def future_set_exception(fut, exc):
    """set exception to future"""

    if future_is_done(fut):
        return

    fut.set_exception(exc)
