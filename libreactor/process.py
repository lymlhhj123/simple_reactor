# coding: utf-8

import os
import shlex
import sys
import signal
import traceback

from .channel import Channel
from . import fd_helper
from . import utils
from . import error


class Process(object):

    def __init__(self, cmd, loop, process_protocol, shell=False, cwd=None, timeout=60):
        """run cmd in subprocess"""

        self.cmd = cmd
        self.loop = loop
        self.shell = shell
        self.protocol = process_protocol
        self.cwd = cwd
        self.timeout = timeout

        self.child_pid = None
        self.stdin_channel = None
        self.stdout_channel = None
        self.stderr_channel = None
        self._channel_closed = 0
        self.timeout_timer = None

        self.loop.call_soon(self._run)

    def _run(self):
        """

        :return:
        """
        stdin_read, stdin_write = fd_helper.make_async_pipe()
        stdout_read, stdout_write = fd_helper.make_async_pipe()
        stderr_read, stderr_write = fd_helper.make_async_pipe()

        pid = os.fork()
        if pid == 0:
            try:
                self._execute_child(stdin_read, stdin_write, stdout_read,
                                    stdout_write, stderr_read, stderr_write)
            except (ValueError, Exception):
                stderr = traceback.format_exc()
                os.write(2, stderr.encode("utf-8"))

            sys.exit(-1)

        self.child_pid = pid

        fd_helper.close_fd(stdin_read)
        fd_helper.close_fd(stdout_write)
        fd_helper.close_fd(stderr_write)

        self.stdin_channel = Channel(stdin_write, self.loop)
        self.stdout_channel = Channel(stdout_read, self.loop)
        self.stderr_channel = Channel(stderr_read, self.loop)

        self.stdout_channel.set_read_callback(self._on_stdout_read)
        self.stderr_channel.set_read_callback(self._on_stderr_read)

        self.stdout_channel.enable_reading()
        self.stderr_channel.enable_reading()

        self.timeout_timer = self.loop.call_later(self.timeout, self._on_timeout)

    def _execute_child(self, stdin_read, stdin_write, stdout_read,
                       stdout_write, stderr_read, stderr_write):
        """

        :return:
        """
        fd_helper.close_fd(stdin_write)
        fd_helper.close_fd(stdout_read)
        fd_helper.close_fd(stderr_read)

        in_dup = os.dup(stdin_read)
        out_dup = os.dup(stdout_write)
        err_dup = os.dup(stderr_write)

        # make sure 0 1 2 is our expected
        os.dup2(in_dup, 0)
        os.dup2(out_dup, 1)
        os.dup2(err_dup, 2)

        try:
            max_fd = os.sysconf("SC_OPEN_MAX")
        except (ValueError, Exception):
            max_fd = 4096

        # close all fd
        os.closerange(3, max_fd)

        if self.cwd:
            os.chdir(self.cwd)

        cmd = self._construct_cmd()

        if os.environ:
            os.execvpe(cmd[0], cmd, os.environ)
        else:
            os.execvp(cmd[0], cmd)

    def _construct_cmd(self):
        """

        :return:
        """
        cmd = self.cmd
        if self.shell is True:
            cmd = ["/bin/sh", "-c"] + [cmd]
        else:
            cmd = shlex.split(cmd)

        return cmd

    def _on_timeout(self):
        """

        :return:
        """
        try:
            self.kill()
        except Exception as e:
            utils.errno_from_ex(e)

        self.timeout_timer = None

    def _on_stdout_read(self):
        """

        :return:
        """
        code, data = self.stdout_channel.read(8192)
        self.protocol.data_received(1, data)

        if error.is_bad_error(code):
            stdout_channel, self.stdout_channel = self.stdout_channel, None
            self._close_channel(stdout_channel)

    def _on_stderr_read(self):
        """

        :return:
        """
        code, data = self.stderr_channel.read(8192)
        self.protocol.data_received(2, data)

        if error.is_bad_error(code):
            stderr_channel, self.stderr_channel = self.stderr_channel, None
            self._close_channel(stderr_channel)

    def _close_channel(self, channel):
        """close stdin/stdout/stderr channel"""
        if channel.is_closed():
            return

        fd = channel.fileno()
        channel.close()
        fd_helper.close_fd(fd)

        self._channel_closed += 1

        if self._channel_closed == 3:
            self._process_exited()

    def _process_exited(self):
        """

        :return:
        """
        try:
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
        except ChildProcessError:
            pid, status = None, -1

        if pid:
            reason = error.Reason(status)
            self.protocol.connection_lost(reason)
        elif pid == 0:
            # what happened ??? try kill
            self.kill()
        else:
            reason = error.Reason(error.ESRCH)
            self.protocol.connection_lost(reason)

    def kill(self):
        """kill child process"""
        self.send_signal(signal.SIGKILL)

    def terminate(self):
        """stop child process"""
        self.send_signal(signal.SIGTERM)

    def send_signal(self, sig):
        """send signal to child process"""
        if not self.child_pid:
            return

        try:
            os.kill(self.child_pid, sig)
        except (OSError, Exception):
            pass
