# coding: utf-8

from libreactor import Protocol


class LineReceiver(Protocol):

    line_sep = "\n"

    def __init__(self):

        super(LineReceiver, self).__init__()

        self._buffer = ""

    def send_line(self, line: str):
        """

        :param line:
        :return:
        """
        if not isinstance(line, str):
            return

        if not line.endswith(self.line_sep):
            line += self.line_sep

        data = line.encode("utf-8")
        self.send_data(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        data = data.decode("utf-8")
        self._buffer += data

        while self._buffer:
            idx = self._buffer.find(self.line_sep)
            if idx == -1:
                break

            # drop `line sep`
            line, self._buffer = self._buffer[:idx], self._buffer[idx + 1:]

            self.line_received(line)

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
