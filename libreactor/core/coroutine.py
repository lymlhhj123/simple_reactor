# coding: utf-8

import types
from functools import wraps

from . import future


def coroutine(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        result_future = future.Future()
        try:
            result = func(*args, **kwargs)
        except StopIteration as e:
            future.future_set_result(result_future, getattr(e, "value", None))
        except Exception as e:
            future.future_set_exception(result_future, e)
        else:
            if isinstance(result, types.GeneratorType):
                try:
                    yielded = next(result)
                except StopIteration as e:
                    future.future_set_result(result_future, getattr(e, "value", None))
                except Exception as e:
                    future.future_set_exception(result_future, e)
                else:
                    _CoroutineScheduler(result, yielded, result_future)
            elif future.is_future(result):
                future.chain_future(result, result_future)
            else:
                future.future_set_result(result_future, result)

        return result_future

    return wrapper


class _CoroutineScheduler(object):

    def __init__(self, gen, yielded, result_future):

        self.gen = gen
        self.future = None
        self.result_future = result_future
        self.finished = False

        self._process_yield(yielded)

    def _process_yield(self, yielded):

        if isinstance(yielded, (list, tuple)):
            self.future = future.multi_future([future.maybe_future(f) for f in yielded])
        else:
            self.future = future.maybe_future(yielded)

        future.future_add_done_callback(self.future, lambda f: self._schedule())

    def _schedule(self):

        if self.finished:
            return

        f = self.future
        self.future = None

        assert future.future_is_done(f)

        try:
            try:
                value = future.future_get_result(f)
            except Exception as e:
                yielded = self.gen.throw(e)
            else:
                yielded = self.gen.send(value)
        except StopIteration as e:
            self.finished = True
            future.future_set_result(self.result_future, getattr(e, "value", None))
            self.result_future = None
        except Exception as e:
            self.finished = True
            future.future_set_exception(self.result_future, e)
            self.result_future = None
        else:
            self._process_yield(yielded)
