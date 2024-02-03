# coding: utf-8

import os
import fcntl


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


def is_fd_async(fd):
    """

    :param fd:
    :return:
    """
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)
    return flag & os.O_NONBLOCK


def close_on_exec(fd, flag=True):
    """

    :param fd:
    :param flag:
    :return:
    """
    flags_old = fcntl.fcntl(fd, fcntl.F_GETFD)
    if flag:
        flag_new = flags_old | fcntl.FD_CLOEXEC
    else:
        flag_new = flags_old & ~fcntl.FD_CLOEXEC

    fcntl.fcntl(fd, fcntl.F_SETFD, flag_new)


def lock_file(fd, *, blocking=True):
    """

    :param fd:
    :param blocking:
    :return:
    """
    flags = fcntl.LOCK_EX
    if blocking is False:
        flags |= fcntl.LOCK_NB

    fcntl.flock(fd, flags)


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


def remove_file(file_path):
    """remove file if exist"""
    try:
        os.remove(file_path)
    except (IOError, OSError):
        pass
