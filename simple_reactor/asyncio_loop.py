# coding: utf-8

import os
import socket
import asyncio
import functools
import collections
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
)

from .tasks import Task
from .options import Options
from . import sock_helper
from . import fd_helper
from . import futures
from .connector import Connector
from .acceptor import Acceptor
from .process import Process
from .common import process_info
from . import sync
from . import queues
from . import io_event
from . import udp
from .context_factory import ContextFactory


class AsyncioLoop(object):

    def __init__(self, asyncio_loop: asyncio.AbstractEventLoop):

        self._loop = asyncio_loop
        self._tid = process_info.get_tid()

        self._reader = set()
        self._writer = set()
        self._channel_map = {}

        self._thread_executor = ThreadPoolExecutor(max_workers=8)
        # set default thread executor
        self._loop.set_default_executor(self._thread_executor)

        self._process_executor = ProcessPoolExecutor(max_workers=8)

    def __getattr__(self, item):
        """forward request to asyncio.AbstractEventLoop"""
        return getattr(self._loop, item)

    def get_asyncio_loop(self):
        """return asyncio loop"""
        return self._loop

    def is_in_loop_thread(self):
        """return True if we are in loop thread"""
        return process_info.get_tid() == self._tid

    def create_future(self):
        """return future attach to loop"""
        return self._loop.create_future()

    def time(self):
        """return loop clock time"""
        return self._loop.time()

    def add_callback(self, fn, *args, **kwargs):
        """add callback run at next loop"""
        callback = functools.partial(fn, *args, **kwargs)
        return self._loop.call_soon(callback)

    call_soon = add_callback

    def call_later(self, delay, fn, *args, **kwargs):
        """add callback run after delay time"""
        return self.call_at(self.time() + delay, fn, *args, **kwargs)

    def call_at(self, when, fn, *args, **kwargs):
        """add callback run at specific time"""
        callback = functools.partial(fn, *args, **kwargs)
        return self._loop.call_at(when, callback)

    call_when = call_at

    def loop_forever(self):
        """run loop forever"""
        self._loop.run_forever()

    run_forever = loop_forever

    def create_lock(self):
        """create coroutine lock"""
        lock = sync.Lock(loop=self)
        return lock

    def create_condition(self, lock=None):
        """create coroutine condition"""
        cond = sync.Condition(loop=self, lock=lock)
        return cond

    def create_event(self):
        """create coroutine event"""
        event = sync.Event(loop=self)
        return event

    def create_fifo_queue(self, max_len=0):
        """create coroutine fifo queue"""
        q = queues.Queue(loop=self, max_len=max_len)
        return q

    def create_priority_queue(self, max_len=0):
        """create coroutine priority queue"""
        q = queues.PriorityQueue(loop=self, max_len=max_len)
        return q

    def create_lifo_queue(self, max_len=0):
        """create coroutine lifo queue"""
        q = queues.LifoQueue(loop=self, max_len=max_len)
        return q

    def create_task(self, coro):
        """wrap coro to task and schedule task to run"""
        fut = self.create_future()
        # add callback to consume coroutine result, nothing to do
        futures.future_add_done_callback(fut, lambda _: None)
        Task(coro, final_future=fut, loop=self)
        return fut

    def run_coroutine_func(self, coroutine, *args, **kwargs):
        """run coroutine function"""
        assert asyncio.iscoroutinefunction(coroutine)

        coro = coroutine(*args, **kwargs)
        return self.create_task(coro)

    def update_channel(self, channel):
        """add channel to loop"""
        fd = channel.fileno()
        if channel.readable():
            if fd not in self._reader:
                self._reader.add(fd)
                self._loop.add_reader(fd, self._handle_events, fd, io_event.EV_READ)
        else:
            if fd in self._reader:
                self._reader.discard(fd)
                self._loop.remove_reader(fd)

        if channel.writable():
            if fd not in self._writer:
                self._writer.add(fd)
                self._loop.add_writer(fd, self._handle_events, fd, io_event.EV_WRITE)
        else:
            if fd in self._writer:
                self._writer.discard(fd)
                self._loop.remove_writer(fd)

        self._channel_map[fd] = channel

    def remove_channel(self, channel):
        """remove channel from loop"""
        fd = channel.fileno()
        if fd not in self._channel_map:
            return

        if fd in self._reader:
            self._reader.discard(fd)
            self._loop.remove_reader(fd)

        if fd in self._writer:
            self._writer.discard(fd)
            self._loop.remove_writer(fd)

        self._channel_map.pop(fd)

    def _handle_events(self, fd, event):
        """handle channel read/write event"""
        channel = self._channel_map[fd]
        channel.handle_events(event)

    async def run_in_thread(self, fn, *args, **kwargs):
        """run fn(*args, **kwargs) in another thread, not block loop"""
        func = functools.partial(fn, *args, **kwargs)
        return await self._loop.run_in_executor(self._thread_executor, func)

    async def run_in_process(self, fn, *args, **kwargs):
        """run fn(*args, **kwargs) in another process, not block loop"""
        func = functools.partial(fn, *args, **kwargs)
        return await self._loop.run_in_executor(self._process_executor, func)

    async def ensure_resolved(self, host, port, *,
                              family=socket.AF_UNSPEC,
                              type_=socket.SOCK_STREAM,
                              proto=socket.IPPROTO_TCP,
                              flags=socket.AI_PASSIVE):
        """resolve host, port to ipaddr pair"""
        addr_info = await self._loop.getaddrinfo(host, port, family=family, type=type_, proto=proto, flags=flags)
        if not addr_info:
            raise ConnectionError(f"Failed to resolve dns {host}:{port}")
        return addr_info

    async def connect_tcp(self, host, port, proto_factory, *,
                          factory=ContextFactory(), options=Options(), ssl_options=None):
        """create tcp client"""
        addr_list = await self.ensure_resolved(host, port)

        remain = collections.deque(addr_list)

        while remain:

            family, sock_type, proto, _, sa = remain.popleft()

            sock = socket.socket(family, sock_type, proto)

            sock_helper.set_sock_async(sock)

            if options.tcp_no_delay:
                sock_helper.set_tcp_no_delay(sock)

            if options.tcp_keepalive:
                sock_helper.set_tcp_keepalive(sock)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            waiter = self._loop.create_future()

            connector = Connector(self, sock, sa, proto_factory, waiter, factory, options, ssl_options)
            connector.connect()
            try:
                return await waiter
            except Exception as e:
                if not remain:
                    raise e

    async def listen_tcp(self, port, proto_factory, *, host=None, factory=ContextFactory(),
                         options=Options(), ssl_options=None):
        """create tcp server"""
        addr_list = await self.ensure_resolved(host, port)

        socks = []
        for res in addr_list:
            af, sock_type, proto, _, sa = res

            sock = socket.socket(af, sock_type, proto)

            if af == socket.AF_INET6:
                # ipv6 socket only accept ipv6 address
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

            sock_helper.set_sock_async(sock)

            if options.reuse_addr:
                sock_helper.set_reuse_addr(sock)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            sock.bind(sa)
            sock.listen(options.backlog)
            socks.append(sock)

        acceptor = Acceptor(self, socks, proto_factory, factory, options, ssl_options)
        acceptor.start()
        return acceptor

    async def connect_udp(self, host, port, proto_factory, *, factory=ContextFactory(), options=Options()):
        """create udp client"""
        addr_list = await self.ensure_resolved(host, port, type_=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

        remain = collections.deque(addr_list)

        while remain:

            family, sock_type, proto, _, sa = remain.popleft()

            sock = socket.socket(family, sock_type, proto)

            sock_helper.set_sock_async(sock)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            if options.allow_broadcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            waiter = self._loop.create_future()

            protocol = proto_factory()
            transport = udp.UDP(self, protocol, sock)
            transport.connect(sa, factory, waiter)

            try:
                await waiter
                return protocol
            except Exception as e:
                if not remain:
                    raise e

    async def listen_udp(self, port, proto_factory, *, host=None, factory=ContextFactory(), options=Options()):
        """create udp server"""
        addr_list = await self.ensure_resolved(host, port, type_=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

        remain = collections.deque(addr_list)
        while remain:
            af, sock_type, proto, _, sa = remain.popleft()

            sock = socket.socket(af, sock_type, proto)

            if af == socket.AF_INET6:
                # ipv6 socket only accept ipv6 address
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

            sock_helper.set_sock_async(sock)

            if options.reuse_addr:
                sock_helper.set_reuse_addr(sock)

            if options.allow_broadcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

            transport = udp.UDP(self, proto_factory(), sock)
            transport.listen(sa, factory)

    async def connect_unix(self, sock_path, proto_factory, *,
                           factory=ContextFactory(), options=Options()):
        """create unix domain client"""

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)
        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        waiter = self.create_future()

        connector = Connector(self, sock, sock_path, proto_factory, waiter, factory, options, None)
        connector.connect()

        return await waiter

    async def listen_unix(self, sock_path, proto_factory, *,
                          mode=0o755, factory=ContextFactory(), options=Options()):
        """create unix domain server"""

        lock_file = sock_path + ".lock"

        lock_fd = open(lock_file, "w")

        if not fd_helper.lock_file(lock_fd, blocking=False):
            raise IOError(f"Failed to lock file: {lock_file}, maybe service already running")

        fd_helper.remove_file(sock_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock_helper.set_sock_async(sock)

        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        if options.reuse_addr:
            sock_helper.set_reuse_addr(sock)

        sock.bind(sock_path)
        os.chmod(sock_path, mode)
        sock.listen(options.backlog)

        acceptor = Acceptor(self, [sock], proto_factory, factory, options, None)
        acceptor.start()
        return acceptor

    async def run_command(self, args, timeout=10):
        """run linux shell command and return (status, stdout, stderr) three tuple"""
        process = await self.subprocess_exec(args, shell=True)

        if timeout and timeout > 0:
            self.call_later(timeout, process.kill)

        stdout, stderr = await process.communicate()

        return_code = process.return_code

        return return_code, stdout, stderr

    async def subprocess_exec(self, args, **kwargs):
        """create subprocess to exec linux shell command"""
        waiter = self.create_future()

        Process(self, args, waiter, **kwargs)

        return await waiter
