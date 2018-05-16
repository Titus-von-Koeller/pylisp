#!/usr/bin/env python3
from operator import add
from collections import Callable

# top -> down evaluation

class Node:
    def __init__(self, value, *children):
        self.value = value
        self.children = children
    def __repr__(self):
        return f'Node({self.value}, *{self.children})'

printr = lambda *a, **kw: print(*a, **kw) # does not evaluate
non_recursing = [printr]

# (print (+ 1 1) (+ 2 2))
x = Node(add, Node(1), Node(1))
y = Node(add, Node(2), Node(2))
n = Node(print, x, y)
p = Node(print, Node(printr, n), n)

def evaluate(AST):
    if isinstance(AST.value, Callable):
        if AST.value not in non_recursing:
            return AST.value(*[evaluate(child) for child in AST.children])
        return AST.value(*AST.children)
    return AST.value
    
evaluate(p)

