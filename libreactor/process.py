# coding: utf-8

import os
import subprocess
from functools import partial
from collections import deque

from .channel import Channel
from . import futures
from . import fd_helper
from . import errors
from . import log

logger = log.get_logger()


class Process(object):

    def __init__(self, loop, args, waiter, **kwargs):

        self.loop = loop
        self.args = args
        self.waiter = waiter
        self.kwargs = kwargs

        self.child_proc = None
        self.channel_map = {}
        self.channel_closed = 0

        self.return_code = None
        self.stdout = b""
        self.stderr = b""
        self.exited_waiters = deque()

        self.loop.call_soon(self._run)

    def _run(self):
        """

        :return:
        """
        stdin_read, stdin_write = fd_helper.make_async_pipe()
        stdout_read, stdout_write = fd_helper.make_async_pipe()
        stderr_read, stderr_write = fd_helper.make_async_pipe()

        wait_close = [stdin_read, stdout_write, stderr_write]
        pipes = [stdin_write, stdout_read, stderr_read]

        try:
            self.child_proc = self._execute_child(stdin_read, stdout_write, stderr_write)
        except Exception as e:
            for fd in pipes:
                fd_helper.close_fd(fd)

            self.return_code = -1
            waiter, self.waiter = self.waiter, None
            futures.future_set_exception(waiter, e)
        else:
            channel = Channel(stdin_write, self.loop)
            channel.set_read_callback(partial(self._on_read, 0))
            channel.enable_reading()
            self.channel_map[0] = channel

            channel = Channel(stdout_read, self.loop)
            channel.set_read_callback(partial(self._on_read, 1))
            channel.enable_reading()
            self.channel_map[1] = channel

            channel = Channel(stderr_read, self.loop)
            channel.set_read_callback(partial(self._on_read, 2))
            channel.enable_reading()
            self.channel_map[2] = channel

            waiter, self.waiter = self.waiter, None
            futures.future_set_result(waiter, self)
        finally:
            for fd in wait_close:
                fd_helper.close_fd(fd)

    def _execute_child(self, in_pipe, out_pipe, err_pipe):
        """create child process"""
        return subprocess.Popen(
            self.args,
            stdin=in_pipe,
            stdout=out_pipe,
            stderr=err_pipe,
            **self.kwargs
        )

    def _on_read(self, fd):
        """called when channel received POLLIN event"""
        if fd == 0:
            channel = self.channel_map.pop(fd)
            channel.disable_all()
            self._close_channel(channel)
        else:  # fd == 1 or 2
            channel = self.channel_map[fd]
            errcode, data = channel.read(8192)

            if errcode in errors.IO_WOULD_BLOCK:
                return

            # pipe closed
            if errcode != errors.OK or not data:
                channel.disable_all()
                self.channel_map.pop(fd)
                self._close_channel(channel)
                return

            if fd == 1:
                self.stdout += data
            else:
                self.stderr += data

    def _close_channel(self, channel):
        """close stdin/stdout/stderr channel"""
        if channel.closed():
            return

        fd = channel.fileno()
        channel.close()
        fd_helper.close_fd(fd)

        self.channel_closed += 1

        self._maybe_finished()

    def _maybe_finished(self):

        if self.channel_closed != 3:
            return

        self.loop.call_soon(self._process_exited)

    def _process_exited(self):
        """

        :return:
        """
        pid = self.child_proc.pid
        try:
            return_pid, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            # maybe child process reaped by signal handler
            logger.error(f"No such process: {pid}")
            return_pid = pid
            status = 0

        if return_pid == 0:
            return

        assert return_pid == pid
        self.child_proc = None

        if os.WIFSIGNALED(status):
            self.return_code = -os.WTERMSIG(status)
        else:
            assert os.WIFEXITED(status)
            self.return_code = os.WEXITSTATUS(status)

        self._wakeup_exited_waiters()

    def _wakeup_exited_waiters(self):
        """wakeup all waiters"""
        while self.exited_waiters:
            fut = self.exited_waiters.popleft()
            futures.future_set_result(fut, None)

    async def communicate(self):
        """wait subprocess end and return (stdout, stderr) tuple"""
        if self.return_code is not None:
            return self.stdout, self.stderr

        await self.wait()

        return self.stdout, self.stderr

    async def wait(self):
        """wait subprocess end return exit code"""
        if self.return_code is not None:
            return self.return_code

        waiter = self.loop.create_future()
        self.exited_waiters.append(waiter)
        await waiter

        return self.return_code

    def kill(self):
        """kill child process"""
        if not self._check_proc():
            return

        self.child_proc.kill()

    def terminate(self):
        """stop child process"""
        if not self._check_proc():
            return

        self.child_proc.terminate()

    def send_signal(self, sig):
        """send signal to child process"""
        if not self._check_proc():
            return

        self.child_proc.send_signal(sig)

    def _check_proc(self):
        """return True if subprocess exist"""
        if not self.child_proc:
            return False
        return True
