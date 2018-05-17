#!/usr/bin/env python3
from operator import add
from collections import Callable

# top -> down evaluation

class Node:
    def __init__(self, value, *children):
        self.value    = value
        self.children = children
    def __repr__(self):
        return f'Node({self.value}, *{self.children})'
    def __call__(self, env=None):
        return self.value(*[child(env=env) for child in self.children])

class Atom(Node):
    def __init__(self, value):
        super().__init__(value)
    def __call__(self, env=None):
        return self.value

class Printr(Node):
    def __init__(self, *children):
        super().__init__(print, *children)
    def __call__(self, env=None):
        return self.value(*self.children)

class Suite(Node):
    def __call__(self, env=None):
        for child in self.children:
            child(env=env)

class Unbound:
    def __init__(self, *children):
        self.children = children
    def __call__(self, env=None):
        if env is None:
            env = {**DEFAULT_ENV}
        value, *children = self.children
        if children:
            node = env[value](*children)
        else:
            node = env[value]
        return node(env=env)

DEFAULT_ENV = {'printr' : Printr, }

# (print (+ 1 1) (+ 2 2))
x = Node(add, Unbound('x'), Atom(1))
y = Node(add, Atom(2), Atom(2))
n = Node(print, x, y)
p = Suite(None, Unbound('printr', n), n)
    
p(env={**DEFAULT_ENV, 'x':Atom(101)})

