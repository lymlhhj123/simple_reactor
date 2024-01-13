# coding: utf-8

import asyncio

from . import futures


class Task(object):

    def __init__(self, coroutine, *, final_future, loop):
        """schedule coroutine to run, coroutine can be made by async/await or yield"""
        self.coro = coroutine
        self.final_future = final_future

        self.loop = loop
        self.await_fut = None
        self.finished = False

        # start to run coroutine
        self.loop.call_soon(self._process_yield, None)

    def _process_yield(self, yielded):
        """handle yield or await object"""
        if isinstance(yielded, (list, tuple)):
            fut_list = []
            for item in yielded:
                fut = self._wrap_to_future(item)
                fut_list.append(fut)

            await_fut = futures.multi_future(fut_list)
        else:
            await_fut = self._wrap_to_future(yielded)

        self.await_fut = await_fut
        futures.future_add_done_callback(await_fut, lambda _: self._schedule())

    def _wrap_to_future(self, yielded):
        """wrap await or yield object to future"""
        if asyncio.iscoroutine(yielded):
            fut = self.loop.create_future()
            Task(yielded, final_future=fut, loop=self.loop)
        else:
            fut = futures.maybe_future(yielded)

        return fut

    def _schedule(self):
        """schedule coro to run"""
        if self.finished:
            return

        # maybe final_future is cancelled
        if futures.future_is_done(self.final_future):
            self.finished = True
            self._coroutine_finished()
            self.final_future = None
            self.await_fut = None
            return

        fut, self.await_fut = self.await_fut, None
        assert futures.future_is_done(fut)

        try:
            try:
                value = futures.future_get_result(fut)
            except Exception as ex:
                yielded = self.coro.throw(ex)
            else:
                yielded = self.coro.send(value)
        except StopIteration as e:
            self._coroutine_finished()
            v = getattr(e, "value", None)
            fut, self.final_future = self.final_future, None
            futures.future_set_result(fut, v)
        except Exception as e:
            self._coroutine_finished()
            fut, self.final_future = self.final_future, None
            futures.future_set_exception(fut, e)
        else:
            self._process_yield(yielded)

    def _coroutine_finished(self):
        """mark coroutine as finished"""
        self.finished = True
        self.loop = None
        self.coro = None
