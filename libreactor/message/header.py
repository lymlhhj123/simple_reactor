# coding: utf-8

import struct


class Header(object):

    CRC32_B = 4
    MSG_B = 4
    EXT_B = 2
    HEADER_LEN = CRC32_B + MSG_B + EXT_B
    HEADER_FMT = "!IIH"  # 4 bytes crc32 + 4 bytes msg len + 2 bytes extension len

    def __init__(self, crc32, msg_len, ext_len):

        self.crc32 = crc32
        self.msg_len = msg_len
        self.ext_len = ext_len

        self.extension = b""

    @classmethod
    def from_buffer(cls, bytes_buffer):
        """

        :param bytes_buffer:
        :return:
        """
        crc32 = bytes_buffer.retrieve_uint32()
        msg_len = bytes_buffer.retrieve_uint32()
        ext_len = bytes_buffer.retrieve_uint16()
        return cls(crc32, msg_len, ext_len)

    def set_extension(self, extension: bytes):
        """

        :param extension:
        :return:
        """
        self.extension = extension

    def is_completed(self):
        """

        :return:
        """
        return len(self.extension) == self.ext_len

    def as_bytes(self):
        """

        :return:
        """
        data = struct.pack(self.HEADER_FMT, self.crc32, self.msg_len, self.ext_len)
        return data + self.extension
