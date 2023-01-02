# coding: utf-8

import zlib
import struct

from .protocol import Protocol

VERSION = 1
HEADER_LEN = 10  # 2 bytes version + 4 bytes crc32 + 4 bytes msg len
HEADER_FMT = "!HII"


class MsgProtocol(Protocol):

    def __init__(self):

        super(MsgProtocol, self).__init__()

        self._buffer = b""
        self._header_retrieved = False
        self._crc32 = 0
        self._msg_len = 0

    def send_msg(self, msg: bytes):
        """

        :param msg:
        :return:
        """
        if isinstance(msg, str):
            msg = msg.encode("utf-8")

        crc32 = zlib.crc32(msg)
        msg_len = len(msg)

        header = struct.pack(HEADER_FMT, VERSION, crc32, msg_len)

        data = header + msg

        self.send_data(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self._buffer += data

        if self._header_retrieved is False:
            if self._retrieve_header() is False:
                return

            self._header_retrieved = True

        if len(self._buffer) < self._msg_len:
            return

        msg, self._buffer = self._buffer[:self._msg_len], self._buffer[self._msg_len:]
        self.msg_received(msg)

        self._header_retrieved = False
        self._crc32, self._msg_len = 0, 0

    def _retrieve_header(self):
        """

        :return:
        """
        if len(self._buffer) < HEADER_LEN:
            return False

        header, self._buffer = self._buffer[:HEADER_LEN], self._buffer[HEADER_LEN:]
        self._crc32, self._msg_len = struct.unpack(HEADER_FMT, header)
        return True

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.context.logger().info(f"{msg}")
