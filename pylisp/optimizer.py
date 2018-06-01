#!/usr/bin/env python3
from .nodes import *
from .insts import *

from copy import deepcopy
from logging import getLogger
logger = getLogger(__name__)

def traverse(tree, func=None):
    if not isinstance(tree, Node):
        return

    if isinstance(tree, Set) \
        and isinstance(tree.value, Lambda):
        func = tree.name

    yield tree, func
    for child in tree.children:
        yield from traverse(child, func)

def constant_folding(tree):
    tree = deepcopy(tree)
    while True:
        did_optimization = False
        for node, _ in traverse(tree):
            if isinstance(node, UNOPS) \
                and not isinstance(node.arg, Var):
                new_node = node(env={})
                node.replace(new_node)
                did_optimization = True
        for node, _ in traverse(tree):
            if isinstance(node, BINOPS) \
                and not isinstance(node.left,  Var) \
                and not isinstance(node.right, Var):
                new_node = node(env={})
                node.replace(new_node)
                did_optimization = True
        if not did_optimization:
            break
    return tree

def identify_tail_calls(tree):
    tree = deepcopy(tree)

    for node, func in traverse(tree):
        if isinstance(node, Ret) \
            and isinstance(node.value, Call) \
            and node.value.name.name == func.name:
            new_node = Ret(TailCall(*node.value.children))
            node.replace(new_node)

    return tree

def optimize_ast(tree, optimizations=(constant_folding, identify_tail_calls)):
    for opt in optimizations:
        tree = opt(tree)
    return tree

def window(xs, size):
    return zip(*(xs[i:] for i in range(size)))

def remove_redundant_stack_ops(bytecodes):
    bytecodes = deepcopy(bytecodes)
    while True:
        did_optimizations = False

        replacements = {}
        for idx, (inst, next_inst) in enumerate(window(bytecodes, 2)):
            if isinstance(inst, PopVar) \
                and isinstance(next_inst, PushVar) \
                and inst.name== next_inst.name:
                replacements[idx, idx+2] = [StoreVar(inst.name)]
                did_optimizations = True

        for (from_idx, to_idx), insts in sorted(replacements.items(), reverse=True):
            bytecodes[from_idx:to_idx] = insts

        if not did_optimizations:
            break

    return bytecodes

def optimize_bytecodes(bytecodes, optimizations=(remove_redundant_stack_ops,)):
    for opt in optimizations:
        bytecodes = opt(bytecodes)
    return bytecodes

__all__ = [
    'constant_folding',
    'identify_tail_calls',
    'optimize_ast',
    'remove_redundant_stack_ops',
    'optimize_bytecodes',
]
