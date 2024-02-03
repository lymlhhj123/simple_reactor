# coding: utf-8

import abc


class BaseTransport(object):

    @abc.abstractmethod
    def fileno(self):
        """return fd belong to this transport"""

    @abc.abstractmethod
    def close(self):
        """close transport"""

    @abc.abstractmethod
    def closed(self):
        """return True if transport is closed"""


class ReadTransport(BaseTransport):

    @abc.abstractmethod
    def pause_reading(self):
        """pause reading data from fd"""

    @abc.abstractmethod
    def resume_reading(self):
        """resume reading data from fd"""

    @abc.abstractmethod
    def read_from_fd(self):
        """reda data from fd"""


class WriteTransport(BaseTransport):

    @abc.abstractmethod
    def set_write_buffer_limits(self, high=None, low=None):
        """set write buffer high and low water"""

    @abc.abstractmethod
    def write_to_fd(self, data):
        """write data to fd"""

    @abc.abstractmethod
    def abort(self):
        """force close fd, drop all buffer data"""


class Transport(ReadTransport, WriteTransport):

    pass


class DatagramTransport(BaseTransport):

    def sendto(self, datagram, address=None):
        """send datagram to address"""

    def abort(self):
        """force close transport"""
