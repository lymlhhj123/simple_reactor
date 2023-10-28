# coding: utf-8

import select

EV_NONE = 0
EV_READ = select.POLLIN
EV_WRITE = select.POLLOUT
EV_ERROR = select.EPOLLERR | select.EPOLLHUP
