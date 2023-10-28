# coding: utf-8

import types
from functools import wraps

from . import futures


def coroutine(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        final_future = futures.create_future()

        try:
            result = func(*args, **kwargs)
        except StopIteration as e:
            val = getattr(e, "value", None)
            futures.future_set_result(final_future, val)
        except Exception as e:
            futures.future_set_exception(final_future, e)
        else:
            if isinstance(result, types.GeneratorType):
                try:
                    first_yielded = next(result)
                except StopIteration as e:
                    val = getattr(e, "value", None)
                    futures.future_set_result(final_future, val)
                except Exception as e:
                    futures.future_set_exception(final_future, e)
                else:
                    _CoroutineScheduler(result, first_yielded, final_future)
            elif futures.is_future(result):
                futures.chain_future(result, final_future)
            else:
                futures.future_set_result(final_future, result)

        return final_future

    return wrapper


class _CoroutineScheduler(object):

    def __init__(self, gen, first_yielded, final_future):

        self.gen = gen
        self.yield_future = None
        self.final_future = final_future
        self.finished = False

        self._process_yield(first_yielded)

    def _process_yield(self, yielded):
        """process yield object, convert to Future"""
        if isinstance(yielded, (list, tuple)):
            self.yield_future = futures.multi_future([futures.maybe_future(f) for f in yielded])
        else:
            self.yield_future = futures.maybe_future(yielded)

        futures.future_add_done_callback(self.yield_future, lambda f: self._schedule())

    def _schedule(self):
        """schedule coroutine to run"""
        if self.finished:
            return

        fut, self.yield_future = self.yield_future, None

        assert futures.future_is_done(fut)

        try:
            try:
                value = futures.future_get_result(fut)
            except Exception as e:
                yielded = self.gen.throw(e)
            else:
                yielded = self.gen.send(value)
        except StopIteration as e:
            self.finished = True
            val = getattr(e, "value", None)
            futures.future_set_result(self.final_future, val)
            self.final_future = None
        except Exception as e:
            self.finished = True
            futures.future_set_exception(self.final_future, e)
            self.final_future = None
        else:
            self._process_yield(yielded)


def sleep(seconds):

    from ._loop_helper import get_event_loop

    f = futures.create_future()

    get_event_loop().call_later(seconds, lambda: futures.future_set_result(f, None))

    return f
