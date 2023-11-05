# coding: utf-8


class Attribute(object):

    def __init__(self, *, excepted_types):

        self.excepted_types = excepted_types

    def __set_name__(self, owner, name):

        self.storage_name = name

    def __get__(self, instance, owner):

        if instance is None:
            return self

        return instance.__dict__[self.storage_name]

    def __set__(self, instance, value):

        if not isinstance(value, self.excepted_types):
            raise TypeError(f"Expected type: {self.excepted_types}, got: {type(value)}")

        instance.__dict__[self.storage_name] = value


class Options(object):

    connect_timeout = Attribute(excepted_types=(int, ))
    tcp_no_delay = Attribute(excepted_types=(bool, ))
    tcp_keepalive = Attribute(excepted_types=(bool, ))
    reuse_addr = Attribute(excepted_types=(bool, ))
    close_on_exec = Attribute(excepted_types=(bool, ))
    backlog = Attribute(excepted_types=(int, ))

    def __init__(self):

        self.connect_timeout = 10
        self.tcp_no_delay = True
        self.tcp_keepalive = True
        self.reuse_addr = True
        self.close_on_exec = True
        self.backlog = 128


class SSLOptions(object):

    server_hostname = Attribute(excepted_types=(str, ))
    cert_file = Attribute(excepted_types=(str, ))
    key_file = Attribute(excepted_types=(str, ))

    def __init__(self):

        self.server_hostname = ""
        self.cert_file = ""
        self.key_file = ""
