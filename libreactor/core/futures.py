# coding: utf-8

from concurrent import futures

Future = futures.Future


def is_future(f):

    return isinstance(f, Future)


def maybe_future(f):

    if is_future(f):
        return f

    result_future = Future()
    future_set_result(result_future, f)
    return result_future


def chain_future(f_in: Future, f_out: Future):

    def copy_result(f):

        assert f is f_in

        if future_is_done(f_out):
            return

        if future_get_exception(f):
            future_set_exception(f_out, future_get_exception(f))
        else:
            future_set_result(f_out, future_get_result(f))

    future_add_done_callback(f_in, copy_result)
    return f_in


def multi_future(fs):

    future = Future()

    waiting_finished = set(fs)

    if not fs:
        future_set_result(future, [])

    def callback(f):

        waiting_finished.discard(f)
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

def future_is_done(future):

    return future.done()


def future_add_done_callback(future, callback):

    from .event_loop import EventLoop

    loop = EventLoop.current()

    future.add_done_callback(lambda f: loop.call_soon(callback, f))


def future_get_result(future):

    return future.result()


def future_set_result(future, value):

    future.set_result(value)


def future_get_exception(future):

    return future.exception()


def future_set_exception(future, exc):

    future.set_exception(exc)
