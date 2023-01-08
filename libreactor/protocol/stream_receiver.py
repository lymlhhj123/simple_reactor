# coding: utf-8

import zlib
import struct

from .protocol import Protocol

VERSION = 1
HEADER_LEN = 10  # 2 bytes version + 4 bytes crc32 + 4 bytes msg len
HEADER_FMT = "!HII"


class Header(object):

    def __init__(self, v, crc32, msg_len):
        """

        :param v:
        :param crc32:
        :param msg_len:
        """
        self.v = v
        self.crc32 = crc32
        self.msg_len = msg_len

    @classmethod
    def from_bytes(cls, data_bytes):
        """

        :param data_bytes:
        :return:
        """
        v, crc32, msg_len = struct.unpack(HEADER_FMT, data_bytes)
        return Header(v, crc32, msg_len)

    def as_bytes(self):
        """

        :return:
        """
        return struct.pack(HEADER_FMT, self.v, self.crc32, self.msg_len)

    def __repr__(self):
        """

        :return:
        """
        return f"{self.v} {self.crc32} {self.msg_len}"


class StreamReceiver(Protocol):

    def __init__(self):

        super(StreamReceiver, self).__init__()

        self._buffer = b""
        self._header = None
        self._header_received = False

    def send_msg(self, msg: bytes):
        """

        :param msg:
        :return:
        """
        if isinstance(msg, str):
            msg = msg.encode("utf-8")

        if not isinstance(msg, bytes):
            self.ctx.logger().error(f"msg type must be str or bytes, not {type(msg)}")
            return

        crc32 = zlib.crc32(msg)
        msg_len = len(msg)

        header = Header(VERSION, crc32, msg_len)

        data = header.as_bytes() + msg

        self.send_data(data)

    def send_data(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self._buffer += data

        if self._header_received is False:
            if self._retrieve_header() is False:
                return

            self._header_received = True

        msg_len = self._header.msg_len
        if len(self._buffer) < msg_len:
            return

        crc32 = self._header.crc32
        try:
            msg, self._buffer = self._buffer[:msg_len], self._buffer[msg_len:]
            if zlib.crc32(msg) != crc32:
                self.msg_broken(self._header, msg)
            else:
                self.msg_received(msg)
        except Exception as e:
            self.ctx.logger().error(f"error happened when process msg, {e}")
        finally:
            self._header_received = False
            self._header = None

    def _retrieve_header(self):
        """

        :return:
        """
        if len(self._buffer) < HEADER_LEN:
            return False

        header_bytes, self._buffer = self._buffer[:HEADER_LEN], self._buffer[HEADER_LEN:]
        try:
            header = Header.from_bytes(header_bytes)
        except Exception as ex:
            self.header_broken(ex)
            return False

        self.header_retrieved(header)
        return True

    def header_broken(self, ex):
        """

        :param ex:
        :return:
        """
        self.ctx.logger().error(f"header broken: {ex}, close connection")
        self.close_connection()

    def header_retrieved(self, header):
        """

        :param header:
        :return:
        """
        self._header = header

    def msg_broken(self, header, msg):
        """

        :param header:
        :param msg:
        :return:
        """
        self.ctx.logger().error(f"msg broken, header: {header}, msg: {msg}, close connection")
        self.close_connection()

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.ctx.logger().info(f"{msg}")
