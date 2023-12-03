# coding: utf-8

from base64 import b64encode

from .utils import to_native_string


def _auth_str(login, password):

    if isinstance(login, str):
        login = login.encode("latin1")

    if isinstance(password, str):
        password = password.encode("latin1")

    cred = b":".join((login, password))
    auth = 'Basic ' + to_native_string(b64encode(cred)).strip()
    return auth


class Auth(object):

    def encode(self):

        raise NotImplementedError


class BasicAuth(Auth):

    def __init__(self, login, password=""):

        if not isinstance(login, (str, bytes)):
            raise ValueError("")

        if not isinstance(password, (str, bytes)):
            raise ValueError()

        self.login = login
        self.password = password

    def encode(self):
        """http basic auth"""
        return _auth_str(self.login, self.password)
