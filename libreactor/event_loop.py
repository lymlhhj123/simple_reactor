# coding: utf-8

import errno
import time
import select
import threading

from . import poller
from .timer import Timer
from .timer_queue import TimerQueue
from .channel import Channel
from .signaler import Signaler
from .callback import Callback
from . import io_event
from . import utils
from .meta import NoConstructor

DEFAULT_TIMEOUT = 3.6  # sec

thread_local = threading.local()


class EventLoop(object):

    def __init__(self, ev_func=None):
        """

        :param ev_func: auto called on every loop
        """
        self._ev_callback = Callback(ev_func) if ev_func else None

        self._time_func = time.monotonic

        self._tid = threading.get_native_id()

        self._mutex = threading.Lock()
        self._callbacks = []
        self._timer_queue = TimerQueue()

        self._channel_map = {}
        self._poller = poller.Poller()

        self.signaler = Signaler()
        self.channel = Channel(self.signaler.fileno(), self)
        self.channel.set_read_callback(self.signaler.read_all)
        self.channel.enable_reading()

    @classmethod
    def current(cls, ev_func=None):
        """

        :param ev_func:
        :return:
        """
        ev = getattr(thread_local, "ev", None)
        if not ev:
            ev = cls(ev_func)
            setattr(thread_local, "ev", ev)

        return ev

    def time(self):
        """

        thread safe
        :return:
        """
        return self._time_func()

    def call_soon(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        with self._mutex:
            self._callbacks.append(cb)

        self.wakeup()

    def call_later(self, delay, func, *args, **kwargs):
        """

        :param delay:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, delay)

    def call_at(self, when, func, *args, **kwargs):
        """

        :param when:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        now = self.time()
        return self.call_later(when - now, func, *args, **kwargs)

    call_when = call_at

    def call_every(self, interval, func, *args, **kwargs):
        """

        :param interval:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, interval, repeated=True)

    def _create_timer(self, cb, delay, repeated=False):
        """

        :param delay:
        :param repeated:
        :param cb:
        :return:
        """
        t = Timer(self, cb, delay, repeated)
        try:
            with self._mutex:
                self._timer_queue.put(t)

            return t
        finally:
            self.wakeup()

    def cancel_timer(self, timer):
        """

        thread safe
        :param timer:
        :return:
        """
        with self._mutex:
            self._timer_queue.cancel(timer)

    def wakeup(self):
        """

        thread safe
        :return:
        """
        if not self.is_in_loop_thread():
            self.signaler.write_one()

    def is_in_loop_thread(self):
        """

        thread safe
        :return:
        """
        return threading.get_native_id() == self._tid

    def update_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        events = 0
        if channel.readable():
            events |= select.POLLIN

        if channel.writable():
            events |= select.POLLOUT

        fd = channel.fileno()
        if fd in self._channel_map:
            self._poller.modify(fd, events)
        else:
            self._channel_map[fd] = channel
            self._poller.register(fd, events)

    def remove_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        fd = channel.fileno()
        if fd not in self._channel_map:
            return

        self._channel_map.pop(fd)
        self._poller.unregister(fd)

    def loop(self):
        """

        :return:
        """
        assert self.is_in_loop_thread()

        while True:
            if self._ev_callback:
                self._ev_callback.run()

            timeout = self._calc_timeout()

            try:
                events = self._poller.poll(timeout)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code != errno.EINTR:
                    break

                events = []

            if events:
                self._handle_events(events)

            self._process_timer_event()

    def _calc_timeout(self):
        """

        :return:
        """
        with self._mutex:
            if self._callbacks:
                return 0.0

            timer = self._timer_queue.first()
            if not timer:
                return DEFAULT_TIMEOUT

        timeout = timer.when - self.time()
        return min(max(0.0, timeout), DEFAULT_TIMEOUT)

    def _handle_events(self, events):
        """

        :param events:
        :return:
        """
        for fd, revents in events:
            ev_mask = 0
            if revents & select.POLLIN:
                ev_mask |= io_event.EV_READ

            if revents & select.POLLOUT:
                ev_mask |= io_event.EV_WRITE

            if revents & (select.POLLERR | select.POLLHUP):
                ev_mask |= (io_event.EV_WRITE | io_event.EV_READ)

            channel = self._channel_map[fd]
            channel.handle_events(ev_mask)

    def _process_timer_event(self):
        """

        :return:
        """
        now = self.time()
        with self._mutex:
            callbacks, self._callbacks = self._callbacks, []
            timer_list = self._timer_queue.retrieve(now)

            # may be cost a lot of time
            # self._timer_queue.resize()

        for cb in callbacks:
            cb.run()

        for timer in timer_list:
            timer.run()
