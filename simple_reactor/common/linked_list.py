# coding: utf-8


class Node(object):

    def __init__(self, v, *, args=None):

        self.value = v
        self.args = args
        self.prev = None
        self.next_ = None


class Empty(Exception):

    pass


class LinkedList(object):

    def __init__(self):

        self.root = Node(None)
        self.root.prev = self.root
        self.root.next_ = self.root

    def add_node(self, node):
        """add node to end"""
        parent = self.root.prev
        child = self.root

        parent.next_ = node
        node.prev = parent

        node.next_ = child
        child.prev = node

    def remove_front(self):
        """remove first node"""
        front = self.front()
        self.remove_node(front)
        return front

    def remove_last(self):
        """remove last node"""
        last = self.last()
        self.remove_node(last)
        return last

    def remove_node(self, node):
        """remove node from list"""
        if node == self.root:
            return

        parent = node.prev
        child = node.next_

        node.prev = None
        node.next_ = None

        parent.next_ = child
        child.prev = parent

    def empty(self):
        """return True if list is empty"""
        return self.root.prev == self.root

    def front(self):
        """return first node, Raise Empty() if list is empty"""
        if self.empty():
            raise Empty("list is empty")

        return self.root.next_

    def last(self):
        """return last node, Raise Empty() if list is empty"""
        if self.empty():
            raise Empty("list is empty")

        return self.root.prev
