#!/usr/bin/env python3
from operator import add, mul, lt, gt, truediv
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
Div    = create_pyfunc(truediv)
Lt     = create_pyfunc(lt)
Gt     = create_pyfunc(gt)

def create_ufunc(args, body, varargs=None):
    class Ufunc(Node):
        def __call__(self, env=None):
            local_env = {**env}
            local_env.update(zip(args, self.children))
            if varargs is not None:
                local_env[varargs] = self.children[len(args):]
            return body(env=local_env)
    return Ufunc

from numbers import Number
from decimal import Decimal, getcontext
getcontext().prec = 11

class Atom(Node):
    def __init__(self, value):
        if isinstance(value, Number):
            value = Decimal(value)
        super().__init__(value)
    def __call__(self, env=None):
        return self.children[0]

class Cell(Node):
    def __init__(self, head, tail):
        super().__init__(Atom(head), Atom(tail))
    head = property(lambda self: self.children[0])
    tail = property(lambda self: self.children[1])
    def __call__(self, env=None):
        return self

class Cons(Node):
    def __init__(self, head, tail):
        super().__init__(head, tail)
    head = property(lambda self: self.children[0])
    tail = property(lambda self: self.children[1])
    def __call__(self, env=None):
        return Cell(self.head(env=env), self.tail(env=env))

class Car(Node):
    def __init__(self, cell):
        super().__init__(cell)
    cell = property(lambda self: self.children[0])
    def __call__(self, env=None):
        return self.cell(env=env).head(env=env)
Head = Car

class Cdr(Node):
    def __init__(self, cell):
        super().__init__(cell)
    cell = property(lambda self: self.children[0])
    def __call__(self, env=None):
        return self.cell(env=env).tail(env=env)
Tail = Cdr

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
            print(value, env[value])
            node = env[value](*children)
        else:
            node = env[value]
        return node(env=env)
Call = Var

class Setq(Node):
    def __call__(self, env=None):
        var, val = self.children 
        val = Atom(val(env=env))
        env[var] = val
        return val

class IfElse(Node):
    def __init__(self, cond, ifbody, elsebody):
        super().__init__(cond, ifbody, elsebody)
    cond     = property(lambda self: self.children[0])
    ifbody   = property(lambda self: self.children[1])
    elsebody = property(lambda self: self.children[2])
    def __call__(self, env=None):
        if self.cond(env=env):
            return self.ifbody(env=env)
        return self.elsebody(env=env)

class While(Node):
    def __init__(self, cond, body):
        super().__init__(cond, body)
    cond = property(lambda self: self.children[0])
    body = property(lambda self: self.children[1])
    def __call__(self, env=None):
        rv = Atom(None)
        while self.cond(env=env):
            rv = self.body(env=env)
        return rv

# class Define(Node):
#     def __call__(self, env=None):
#         var, val = self.children 
#         env[var] = val
#         return val

Lambda = create_ufunc
VarArgsLambda = lambda args, body, varargs: create_ufunc(args, body, varargs)

DEFAULT_ENV = {'printr' : Printr, }

f = Setq('f', Lambda(['x'], Suite(
    Print(Atom('inside f before'), Var('x')),
    Setq('x', Div(Var('x'), Atom(3))),
    Call('g', Var('x')),
    Print(Atom('inside f after'), Var('x')),
    )))

g = Setq('g', Lambda(['x'], Suite(
    Print(Atom('inside g before'), Var('x')),
    Setq('x', Div(Var('x'), Atom(3))),
    Call('h', Var('x')),
    Print(Atom('inside g after'), Var('x')),
    )))

h = Setq('h', Lambda(['x'], Suite(
    Print(Atom('inside h before'), Var('x')),
    Setq('x', Div(Var('x'), Atom(3))),
    # Call('g', Var('x')),
    Print(Atom('inside h after'), Var('x')),
    )))

s = Setq(
    'sum', 
    VarArgsLambda(
        [], 
        'nums', 
        Suite(
            Print(Var('nums')),
        )
    )
)
    
p = {
'var_args' : Suite(
    s,
    Call('sum', Atom(1), Atom(2), Atom(3))
),

'func_call' : Suite(
    Setq('x', Atom(1)),
    h,
    g,
    f,
    Call('f', Var('x')),
    Setq('y', Atom(-1)),
    IfElse(Lt(Var('y'), Atom(0)), Print(Atom('Smaller')), Print(Atom('Bigger')))
    ),

'loop' : Suite(
    Setq('x', Atom(10000)),
    While(
        Gt(Var('x'), Atom(0)), 
        Suite(
            Print(Var('x')),
            Setq('x', Add(Var('x'), Atom(-1)))
        )
    )),

'cons' : Suite(
    Setq(
        'x', 
        Cons(
            Atom(1),
            Atom('a')
        )
    ),
    Print(Atom('Car:'), Car(Var('x'))),
    Print(Atom('Cdr:'), Cdr(Var('x'))),
    ),
}

test = 'var_args' 
try:
    rv = p[test](env={**DEFAULT_ENV})
except Exception:
    from pdb import post_mortem
    # post_mortem()
    raise
    
print(f'rv = {rv}')
