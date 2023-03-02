# coding: utf-8

from .protocol import Protocol


class _BaseContext(object):

    protocol_cls = Protocol

    def __init__(self):

        self.on_error = None
        self.on_failure = None
        self.on_closed = None

    def set_error_callback(self, on_error):
        """

        :param on_error:
        :return:
        """
        self.on_error = on_error

    def set_failure_callback(self, on_failure):
        """

        :param on_failure:
        :return:
        """
        self.on_failure = on_failure

    def set_closed_callback(self, on_closed):
        """

        :param on_closed:
        :return:
        """
        self.on_closed = on_closed

    def connection_error(self, conn):
        """
        auto called when connection error happened
        :return:
        """
        if self.on_error:
            self.on_error(conn)

    def connection_failure(self, conn):
        """
        auto called when connection can not be established
        :return:
        """
        if self.on_failure:
            self.on_failure(conn)

    def connection_closed(self, conn):
        """

        :param conn:
        :return:
        """
        if self.on_closed:
            self.on_closed(conn)

    def build_protocol(self):
        """

        :return:
        """
        return self.protocol_cls()


class ClientContext(_BaseContext):
    
    def __init__(self):
        
        super(ClientContext, self).__init__()

        self.on_established = None

    def set_established_callback(self, on_established):
        """

        :param on_established:
        :return:
        """
        self.on_established = on_established

    def connection_established(self, protocol):
        """

        auto called when client connection established
        :param protocol:
        :return:
        """
        if self.on_established:
            self.on_established(protocol)


class ServerContext(_BaseContext):

    def __init__(self):
        
        super(ServerContext, self).__init__()

        self.on_made = None

    def set_made_callback(self, on_made):
        """

        :param on_made:
        :return:
        """
        self.on_made = on_made

    def connection_made(self, protocol):
        """

        auto called when server side connection made
        :param protocol:
        :return:
        """
        if self.on_made:
            self.on_made(protocol)
