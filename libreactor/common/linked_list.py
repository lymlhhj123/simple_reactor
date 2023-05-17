# coding: utf-8


class Node(object):

    def __init__(self, v, prev=None, next_=None):
        """

        :param v:
        :param prev:
        :param next_:
        """
        self.v = v
        self.prev = prev
        self.next_ = next_


class LinkedList(object):

    def __init__(self):

        self.root = Node(None)
        self.root.prev = self.root
        self.root.next_ = self.root

    def add_node(self, node):
        """

        :param node:
        :return:
        """
        self._add_node(self.root.prev, node, self.root)

    def _add_node(self, parent, node, child):
        """

        :param parent:
        :param node:
        :param child:
        :return:
        """
        parent.next_ = node
        node.prev = parent

        node.next_ = child
        child.prev = node

    def remove_node(self, node):
        """

        :param node:
        :return:
        """
        self._remove_node(node.prev, node, node.next_)

    def _remove_node(self, parent, node, child):
        """

        :param parent:
        :param node:
        :param child:
        :return:
        """
        node.prev = None
        node.next_ = None

        parent.next_ = child
        child.prev = parent

    def empty(self):
        """

        :return:
        """
        return self.root.prev == self.root

    def front(self):
        """

        :return:
        """
        return self.root.next_