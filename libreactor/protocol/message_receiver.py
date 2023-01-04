# coding: utf-8

import zlib
import struct

from .stream import Stream

VERSION = 1
HEADER_LEN = 10  # 2 bytes version + 4 bytes crc32 + 4 bytes msg len
HEADER_FMT = "!HII"


class MessageReceiver(Stream):

    def __init__(self):

        super(MessageReceiver, self).__init__()

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

        if not isinstance(msg, bytes):
            self.context.logger().error(f"msg type must be str or bytes, not {type(msg)}")
            return

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

        try:
            msg, self._buffer = self._buffer[:self._msg_len], self._buffer[self._msg_len:]
            if zlib.crc32(msg) != self._crc32:
                self.context.logger().error("msg broken, drop it")
                return

            self.msg_received(msg)
        except Exception as e:
            self.context.logger().error(f"error happened when handle msg, {e}")
        finally:
            self._clear_header()

    def _retrieve_header(self):
        """

        :return:
        """
        if len(self._buffer) < HEADER_LEN:
            return False

        header, self._buffer = self._buffer[:HEADER_LEN], self._buffer[HEADER_LEN:]
        _, self._crc32, self._msg_len = struct.unpack(HEADER_FMT, header)
        return True

    def _clear_header(self):
        """

        :return:
        """
        self._header_retrieved = False
        self._crc32, self._msg_len = 0, 0

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.context.logger().info(f"{msg}")
