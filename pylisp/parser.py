#!/usr/bin/env python3
from re import escape, compile
from pprint import pformat
from logging import getLogger
logger = getLogger(__name__)

NAME     = '[^"\'() \n\t]+'
QUOTED   = r'"(?:[^"\\]|\\.)*"'
LPAREN   = "'?" + escape('(')
RPAREN   = escape(')')
TOKEN    = f'({NAME}|{QUOTED}|{LPAREN}|{RPAREN})'
TOKEN_RE = compile(TOKEN)

def tokenize(s):
    for token in TOKEN_RE.split(s):
        if token.strip():
            yield token
    return

def build_tree(tokens):
    rv = []
    current = [rv]
    for value in tokens:
        if value == '(':
            t = []
            current[-1].append(t)
            current.append(t)
        elif value == "'(":
            t = ['quoted', []]
            current[-1].append(t)
            current.append(t[-1])
        elif value == ')':
            current.pop()
        else:
            current[-1].append(value)
    return rv

def build_nodes(tree):
    from .nodes import Node
    return Node.parse(tree)

def build_ast(tokens):
    tree = build_tree(tokens)
    logger.info('tree:\n%s', pformat(tree))
    nodes = build_nodes(tree)
    logger.info('nodes:\n%s', pformat(nodes))
    return nodes

def parse(s):
    tokens = list(tokenize(s))
    logger.info('tokens\n%s', pformat(tokens))
    ast = build_ast(tokens)
    return ast

__all__ = 'parse',
