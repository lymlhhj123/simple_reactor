# coding: utf-8

from concurrent import futures

Future = futures.Future


def is_future(f):

    return isinstance(f, Future)


def maybe_future(f):

    if is_future(f):
        return f

    f = Future()
    f.set_result(f)
    return f


def chain_future(f_in: Future, f_out: Future):

    def set_result(f):

        assert f is f_in

        if f_out.done():
            return

        if f_in.exception():
            f_out.set_exception(f_in.exception())
        else:
            f_out.set_result(f_in.result())

    f_in.add_done_callback(set_result)
    return f_in


def multi_future(fs):

    future = Future()

    waiting_finished = set(fs)

    def callback(f):

        waiting_finished.discard(f)
        if waiting_finished:
            return

        result_list = []
        for f in fs:
            try:
                result = f.result()
            except Exception as e:
                if not future.done():
                    future.set_exception(e)
                    break
            else:
                result_list.append(result)

        if not future.done():
            future.set_result(result_list)

    for child in waiting_finished:
        child.add_done_callback(callback)

    return future
