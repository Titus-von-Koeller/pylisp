#!/usr/bin/env python3
from .frame import Frame

from copy import deepcopy
from collections import ChainMap
from logging import getLogger
logger = getLogger(__name__)

class Inst:
    def __init__(self, *children):
        self.children = children
    def __repr__(self):
        return f'{type(self).__name__}({", ".join(repr(x) for x in self.children)})'
    def __deepcopy__(self, memo=None):
        return type(self)(*deepcopy(self.children, memo))

class Noop(Inst):
    def __call__(self):
        pass

class Missing(Inst):
    def __init__(self, node):
        super().__init__(node)
    node = property(lambda self: self.children[0])
    def __call__(self, frames):
        raise NotImplementedError(f'unimplemented bytecode for {self.node}')

class CallPyFunc(Inst):
    def __init__(self, func, args):
        super().__init__(func, args)
    func = property(lambda self: self.children[0])
    args = property(lambda self: self.children[1])
    def __call__(self, frames):
        args = [frames[-1].pop() for _ in range(self.args)]
        rv = self.func(*args)
        frames[-1].push(rv)

class Halt(Inst):
    def __init__(self, catch_fire=False):
        super().__init__(catch_fire)
    catch_fire = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames.clear()

class PushImm(Inst):
    def __init__(self, value):
        super().__init__(value)
    value = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames[-1].push(self.value)

class PushVar(Inst):
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames[-1].push(frames[-1].env[self.name])

class PopVar(Inst):
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames[-1].env[self.name] = frames[-1].pop()

class StoreVar(Inst):
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames[-1].env[self.name] = frames[-1].peek()

class Label(Inst):
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        pass

class JumpAlways(Inst):
    def __init__(self, label):
        super().__init__(label)
    label = property(lambda self: self.children[0])
    def __call__(self, frames):
        frames[-1].jump(self.label)

class JumpIfTrue(Inst):
    def __init__(self, label):
        super().__init__(label)
    label = property(lambda self: self.children[0])
    def __call__(self, frames):
        val = frames[-1].pop()
        if val:
            frames[-1].jump(self.label)

class JumpIfFalse(Inst):
    def __init__(self, label):
        super().__init__(label)
    label = property(lambda self: self.children[0])
    def __call__(self, frames):
        val = frames[-1].pop()
        if not val:
            frames[-1].jump(self.label)

class Ufunc(Inst):
    def __init__(self, params, body, closures):
        super().__init__(params, body, closures)
    params   = property(lambda self: self.children[0])
    body     = property(lambda self: self.children[1])
    closures = property(lambda self: self.children[2])
    def __call__(self, frames):
        pass

class CreateFunc(Inst):
    def __init__(self, params, body):
        super().__init__(params.value, [*body, PopFunc()])
    params = property(lambda self: self.children[0])
    body   = property(lambda self: self.children[1])
    def __call__(self, frames):
        if isinstance(frames[-1].env, ChainMap):
            closures = frames[-1].env.maps[:-1]
        else:
            closures = []
        func = Ufunc(self.params, self.body, closures)
        frames[-1].push(func)

class PushFunc(Inst):
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def prepare(self, frames):
        func = frames[-1].env[self.name]
        local_env = {}
        for n in func.params:
            local_env[n] = frames[-1].pop()
        outer_env = frames[-1].env
        if isinstance(outer_env, ChainMap):
            env = ChainMap(local_env, *func.closures, outer_env.maps[-1])
        else:
            env = ChainMap(local_env, *func.closures, outer_env)
        return func, env
    def __call__(self, frames):
        func, env = self.prepare(frames)

        frame = Frame(func.body, env=env, stats=frames[-1].stats)
        frames.append(frame)

        # stats
        stats = frames[-1].stats
        stats.func_calls += 1
        stats.num_frames += 1
        stats.max_frame_depth = max(stats.max_frame_depth, len(frames))

class PushTailFunc(PushFunc):
    def __call__(self, frames):
        func, env = self.prepare(frames)

        frame = frames[-1]
        frame.pc = 0
        frame.env = env

        # stats
        stats = frames[-1].stats
        stats.func_calls += 1
        stats.num_frames += 0
        stats.max_frame_depth = max(stats.max_frame_depth, len(frames))

class PushRawFunc(Inst):
    def __init__(self, insts, names=(), pc=0, stack=None, env=None):
        super().__init__(insts, names, pc, stack, env)
    insts = property(lambda self: self.children[0])
    names = property(lambda self: self.children[1])
    pc    = property(lambda self: self.children[2])
    stack = property(lambda self: self.children[3])
    env   = property(lambda self: self.children[4])
    def __call__(self, frames):
        if self.env is None:
            local_env = {}
        else:
            local_env = self.env
        for n in self.names:
            local_env[n] = frames[-1].pop()
        outer_env = frames[-1].env
        if isinstance(outer_env, ChainMap):
            env = ChainMap(local_env, outer_env.maps[-1])
        else:
            env = ChainMap(local_env, outer_env)
        frame = Frame(self.insts, self.pc, self.stack, env, stats=frames[-1].stats)
        frames.append(frame)

        # stats
        stats = frames[-1].stats
        stats.func_calls += 1
        stats.num_frames += 1
        stats.max_frame_depth = max(stats.max_frame_depth, len(frames))

class PopFunc(Inst):
    def __init__(self, name=None):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        if self.name is not None:
            rv = frames[-1].env[self.name]
        else:
            rv = frames[-1].pop()
        frames.pop()
        if frames: frames[-1].push(rv)

__all__ = [
    'Inst', 'Noop', 'Missing', 'CallPyFunc', 'Halt',
    'PushImm', 'PushVar', 'PopVar', 'StoreVar', 'Label',
    'JumpAlways', 'JumpIfTrue', 'JumpIfFalse', 'Ufunc',
    'CreateFunc', 'PushFunc', 'PushTailFunc', 'PushRawFunc', 'PopFunc',
]
