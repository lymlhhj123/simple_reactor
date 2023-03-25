# coding: utf-8

import struct


class Header(object):

    CRC32_B = 4
    MSG_B = 4
    EXT_B = 2
    HEADER_LEN = CRC32_B + MSG_B + EXT_B
    HEADER_FMT = "!IIH"  # 4 bytes crc32 + 4 bytes msg len + 2 bytes extension len

    def __init__(self, crc32, msg_len):
        """

        :param crc32:
        :param msg_len:
        """
        self._crc32 = crc32
        self._msg_len = msg_len

        self._ext_len = 0
        self._extension = b""

    @classmethod
    def from_buffer(cls, bytes_buffer):
        """

        :param bytes_buffer:
        :return:
        """
        crc32 = bytes_buffer.retrieve_uint32()
        msg_len = bytes_buffer.retrieve_uint32()
        ext_len = bytes_buffer.retrieve_uint16()
        header = cls(crc32, msg_len)
        header.set_ext_len(ext_len)
        return header

    def set_ext_len(self, ext_len):
        """

        :param ext_len:
        :return:
        """
        self._ext_len = ext_len

    def set_extension(self, extension: bytes):
        """

        :param extension:
        :return:
        """
        assert isinstance(extension, bytes)
        self._extension = extension

    def crc32(self):
        """

        :return:
        """
        return self._crc32

    def msg_len(self):
        """

        :return:
        """
        return self._msg_len

    def ext_len(self):
        """

        :return:
        """
        return self._ext_len

    def extension(self):
        """

        :return:
        """
        return self._extension

    def is_completed(self):
        """

        :return:
        """
        return len(self._extension) == self._ext_len

    def as_bytes(self):
        """

        :return:
        """
        data = struct.pack(self.HEADER_FMT, self._crc32, self._msg_len, self._ext_len)
        return data + self._extension
