# coding: utf-8

import types
from functools import wraps

from .future import Future, is_future


def coroutine(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        f = Future()
        try:
            result = func(*args, **kwargs)
        except StopIteration as e:
            f.set_result(getattr(e, "value", None))
        except Exception as e:
            f.set_exception(e)
        else:
            if isinstance(result, types.GeneratorType):
                try:
                    yield_future = next(result)
                except StopIteration as e:
                    f.set_result(getattr(e, "value", None))
                except Exception as e:
                    f.set_exception(e)
                else:
                    _CoroutineScheduler(result, yield_future, f)
            elif is_future(result):
                f = result
            else:
                f.set_result(result)

        return f

    return wrapper


class _CoroutineScheduler(object):

    def __init__(self, gen, yielded, result_future):

        self.gen = gen
        self.future = None
        self.result_future = result_future
        self.finished = False
        self.running = False

        if self._process_yield(yielded):
            self._schedule()

    def _process_yield(self, yielded):

        if isinstance(yielded, (list, tuple)):
            self.future = multi_future(yielded)
        else:
            self.future = yielded

        if not self.future.done():
            self.future.add_done_callback(self._schedule)
            return False

        return True

    def _schedule(self):

        if self.running or self.finished:
            return

        self.running = True
        try:
            self._run_coroutine()
        finally:
            self.running = False

    def _run_coroutine(self):

        while 1:
            if not self.future.done():
                return

            try:
                try:
                    value = self.future.result()
                except Exception as e:
                    yielded = self.gen.throw(e)
                else:
                    yielded = self.gen.send(value)
            except StopIteration as e:
                self.finished = True
                self.result_future.set_result(getattr(e, "value", None))
                self.result_future = None
                return
            except Exception as e:
                self.finished = True
                self.result_future.set_exception(e)
                self.result_future = None
                return

            if not self._process_yield(yielded):
                return


def multi_future(future_list):

    new_future = Future()

    waiting_finished = set(future_list)

    def callback(f):

        waiting_finished.discard(f)
        if waiting_finished:
            return

        result_list = []
        for f in future_list:
            try:
                result = f.result()
            except Exception as e:
                if not new_future.done():
                    new_future.set_exception(e)
                    break
            else:
                result_list.append(result)

        if not new_future.done():
            new_future.set_result(result_list)

    for child in waiting_finished:
        child.add_done_callback(callback)

    return new_future
