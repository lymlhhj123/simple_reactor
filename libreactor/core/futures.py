# coding: utf-8

from concurrent import futures as __futures

__Future = __futures.Future


def create_future():

    return __Future()


def is_future(f):

    return isinstance(f, __Future)


def maybe_future(fut):

    if is_future(fut):
        return fut

    proxy = create_future()
    future_set_result(proxy, fut)
    return proxy


def wait_timeout(fut, timeout):
    """wait fut complete or timeout"""
    from ._loop_helper import get_event_loop

    def timeout_callback():
        if future_is_done(fut):
            return

        fut.set_exception(TimeoutError("future timeout"))

    loop = get_event_loop()
    handle = loop.call_later(timeout, timeout_callback)
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

    future = create_future()

    waiting_finished = set(fs)

    if not fs:
        future_set_result(future, [])

    def callback(fut):

        waiting_finished.discard(fut)
        if waiting_finished:
            return

        result_list = []
        for f in fs:
            try:
                result = future_get_result(f)
            except Exception as e:
                if not future_is_done(future):
                    future_set_exception(future, e)
                    break
            else:
                result_list.append(result)

        if not future.done():
            future_set_result(future, result_list)

    children = set()
    for child in fs:
        if child in children:
            continue

        children.add(child)
        future_add_done_callback(child, callback)

    return future


# future helper function

def future_is_done(fut):

    return fut.done()


def future_add_done_callback(fut, callback):

    from ._loop_helper import get_event_loop

    loop = get_event_loop()

    fut.add_done_callback(lambda f: loop.call_soon(callback, f))


def future_get_result(fut):

    return fut.result()


def future_set_result(fut, value):

    fut.set_result(value)


def future_get_exception(fut):

    return fut.exception()


def future_set_exception(fut, exc):

    fut.set_exception(exc)
