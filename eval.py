#!/usr/bin/env python3
from operator import add, mul
from collections import Callable

# top -> down evaluation

class Node:
    def __init__(self, *children, env=None):
        self.children = children
    def __repr__(self):
        return f'{type(self).__name__}(*{self.children})'

def create_pyfunc(func, recurse=True):
    class Pyfunc(Node):
        def __call__(self, env=None):
            args = self.children
            if recurse:
                return func(*[child(env=env) for child in args])
            else:
                return func(*args)
    return Pyfunc
Print  = create_pyfunc(print)
Printr = create_pyfunc(print, recurse=False)
Add    = create_pyfunc(add)
Mul    = create_pyfunc(mul)

def create_ufunc(args, body):
    class Ufunc(Node):
        def __call__(self, env=None):
            local_env = {**env}
            local_env.update(zip(args, self.children))
            return body(env=local_env)
    return Ufunc

class Atom(Node):
    def __init__(self, value):
        super().__init__(value)
    def __call__(self, env=None):
        return self.children[0]

class Suite(Node):
    def __call__(self, env=None):
        for child in self.children:
            child(env=env)

class Var(Node):
    def __call__(self, env=None):
        if env is None:
            env = {**DEFAULT_ENV}
        value, *children = self.children
        if children:
            node = env[value](*children)
        else:
            node = env[value]
        return node(env=env)

class Setq(Node):
    def __call__(self, env=None):
        var, val = self.children 
        val = Atom(val())
        env[var] = val
        return val

class Define(Node):
    def __call__(self, env=None):
        var, val = self.children 
        env[var] = val
        return val

class Lambda(Node):
    def __init__(self, args, body):
        super().__init__(args, body)
    def __call__(self, env=None):
        args, body = self.children
        return create_ufunc(args, body)


DEFAULT_ENV = {'printr' : Printr, }

p = Suite(
    Setq('x', Atom('str')),
    Define('repeat', Lambda(['x'], Mul(Var('x'), Atom(3)))),
    Print(Var('repeat', Var('x'))),
    )

# (define add3 (lambda (x y z) (+ x (+ y z)))
rv = p(env={**DEFAULT_ENV})
print(f'rv = {rv}')
