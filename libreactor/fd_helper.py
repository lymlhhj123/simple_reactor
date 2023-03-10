# coding: utf-8

import errno
import os
import fcntl

from .const import ErrorCode
from .utils import errno_from_ex


def make_async_pipe():
    """

    :return:
    """
    r, w = os.pipe()

    make_fd_async(r)
    make_fd_async(w)

    close_on_exec(r)
    close_on_exec(w)

    return r, w


def make_fd_async(fd):
    """

    :param fd:
    :return:
    """
    flag_old = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag_old | os.O_NONBLOCK)


def close_on_exec(fd):
    """

    :param fd:
    :return:
    """
    flags_old = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags_old | fcntl.FD_CLOEXEC)


def lock_file(fd, blocking=True):
    """

    :param fd:
    :param blocking:
    :return:
    """
    flags = fcntl.LOCK_EX
    if blocking is False:
        flags |= fcntl.LOCK_NB

    try:
        fcntl.flock(fd, flags)
        return True
    except (IOError, OSError):
        return False


def unlock_file(fd):
    """

    :param fd:
    :return:
    """
    fcntl.flock(fd, fcntl.LOCK_UN)


def close_fd(fd):
    """

    :param fd:
    :return:
    """
    try:
        os.close(fd)
    except (IOError, OSError):
        pass


def read_fd(fd, chunk_size=8192):
    """
    read non-block fd until buffer is empty
    :param fd:
    :param chunk_size:
    :return:
    """
    output = b""
    while True:
        err_code, data = read_once(fd, chunk_size)
        if err_code != ErrorCode.OK:
            break

        output += data

    return err_code, output


def read_once(fd, chunk_size=8192):
    """
    read non-block fd once
    :param fd:
    :param chunk_size:
    :return:
    """
    try:
        data = os.read(fd, chunk_size)
    except IOError as e:
        err_code = errno_from_ex(e)
        if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
            err_code = ErrorCode.DO_AGAIN

        return err_code, b""

    if not data:
        return ErrorCode.CLOSED, b""

    return ErrorCode.OK, data


def write_fd(fd, data: bytes):
    """
    write non-block fd
    :param fd:
    :param data:
    :return:
    """
    idx = 0
    while True:
        err_code, chunk_size = write_once(fd, data[idx:])
        if err_code != ErrorCode.OK:
            return err_code, idx

        idx += chunk_size
        if idx == len(data):
            return ErrorCode.OK, idx


def write_once(fd, data: bytes):
    """

    :param fd:
    :param data:
    :return:
    """
    try:
        chunk_size = os.write(fd, data)
    except IOError as e:
        err_code = errno_from_ex(e)
        if err_code == errno.EAGAIN or err_code == errno.EWOULDBLOCK:
            err_code = ErrorCode.DO_AGAIN, 0

        return err_code, 0

    if chunk_size == 0:
        return ErrorCode.CLOSED, 0

    return ErrorCode.OK, chunk_size
