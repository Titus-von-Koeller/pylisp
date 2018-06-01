#!/usr/bin/env python3
from logging import getLogger
logger = getLogger(__name__)

class Stats:
    def __init__(self):
        self.func_calls = 0
        self.num_frames = 0
        self.max_frame_depth = 0
        self.num_insts = 0
    def __repr__(self):
        return f'Stats(func_calls={self.func_calls!r}, num_frames={self.num_frames!r}, max_frame_depth={self.max_frame_depth!r}, num_insts={self.num_insts!r})'

class Frame:
    def __init__(self, insts, pc=0, stack=None, env=None, stats=None):
        from .nodes import Label
        self.insts = insts
        self.labels = {inst.name: idx for idx, inst in enumerate(insts)
                       if isinstance(inst, Label)}
        self.pc = pc
        if stack is None:
            stack = []
        self.stack = stack
        if env is None:
            env = {}
        self.env = env
        if stats is None:
            stats = Stats()
        self.stats = stats
    def __iter__(self):
        self.pc = 0
        return self
    def __next__(self):
        if self.pc is None or not (0 <= self.pc < len(self.insts)):
            raise StopIteration()
        inst = self.insts[self.pc]
        self.pc += 1
        return inst
    def __repr__(self):
        return f'Frame(insts={self.insts!r}, pc={self.pc!r}, stack={self.stack!r}, env={self.env!r})'
    def peek(self):
        return self.stack[-1]
    def push(self, value):
        self.stack.append(value)
    def pop(self):
        return self.stack.pop()
    def jump(self, label):
        self.pc = self.labels[label]

__all__ = [
    'Frame',
    'Stats',
]
