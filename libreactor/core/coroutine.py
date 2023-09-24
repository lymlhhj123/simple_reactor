# coding: utf-8

import types
from functools import wraps

from . import future_mixin


def coroutine(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        result_future = future_mixin.Future()
        try:
            result = func(*args, **kwargs)
        except StopIteration as e:
            val = result_future, getattr(e, "value", None)
            future_mixin.future_set_result(result_future, val)
        except Exception as e:
            future_mixin.future_set_exception(result_future, e)
        else:
            if isinstance(result, types.GeneratorType):
                try:
                    yielded = next(result)
                except StopIteration as e:
                    val = result_future, getattr(e, "value", None)
                    future_mixin.future_set_result(result_future, val)
                except Exception as e:
                    future_mixin.future_set_exception(result_future, e)
                else:
                    _CoroutineScheduler(result, yielded, result_future)
            elif future_mixin.is_future(result):
                future_mixin.chain_future(result, result_future)
            else:
                future_mixin.future_set_result(result_future, result)

        return result_future

    return wrapper


class _CoroutineScheduler(object):

    def __init__(self, gen, yielded, result_future):

        self.gen = gen
        self.future = None
        self.result_future = result_future
        self.finished = False

        if self._process_yield(yielded):
            self._schedule()

    def _process_yield(self, yielded):
        """process yield object, convert to Future"""
        if isinstance(yielded, (list, tuple)):
            self.future = future_mixin.multi_future([future_mixin.maybe_future(f) for f in yielded])
        else:
            self.future = future_mixin.maybe_future(yielded)

        if future_mixin.future_is_done(self.future):
            return True

        future_mixin.future_add_done_callback(self.future, lambda f: self._schedule())
        return False

    def _schedule(self):
        """schedule coroutine to run"""
        if self.finished:
            return

        while True:
            f = self.future

            if not future_mixin.future_is_done(f):
                return

            self.future = None

            try:
                try:
                    value = future_mixin.future_get_result(f)
                except Exception as e:
                    yielded = self.gen.throw(e)
                else:
                    yielded = self.gen.send(value)
            except StopIteration as e:
                self.finished = True
                val = getattr(e, "value", None)
                future_mixin.future_set_result(self.result_future, val)
                self.result_future = None
                return
            except Exception as e:
                self.finished = True
                future_mixin.future_set_exception(self.result_future, e)
                self.result_future = None
                return
            else:
                if not self._process_yield(yielded):
                    return


def sleep(seconds):

    from .event_loop import EventLoop

    f = future_mixin.Future()

    EventLoop.current().call_later(seconds, lambda: future_mixin.future_set_result(f, None))

    return f
