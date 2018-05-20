#!/usr/bin/env python3
from textwrap import indent, dedent
from collections import defaultdict
from functools import wraps
from logging import getLogger
from pprint import pformat
logger = getLogger(__name__)

# NOT thread-safe!!
depth = 0
max_depth = 30
max_length = len('Comment')
stats = {'func-calls': defaultdict(int), 'ufunc-calls': defaultdict(int)}
def print_stats():
    if stats['func-calls']:
        print('Function Calls')
        print('--------------')
        width = max(len(str(x)) for x in stats['func-calls'])
        for cls, count in sorted(stats['func-calls'].items()):
            print(f'\t{cls:<{width}} = {count}')
    if stats['ufunc-calls']:
        print('User Defined Function Calls')
        print('---------------------------')
        width = max(len(str(x)) for x in stats['ufunc-calls'])
        for obj, count in sorted(stats['ufunc-calls'].items()):
            print(f'\t{obj:<{width}} = {count}')
def debug(f):
    @wraps(f)
    def inner(self, env):
        global depth
        call_indent = '  ' * depth
        template = f'%-{max_depth}s:%-{max_length}s:env = %r'
        logger.debug(template, f'{call_indent}enter', type(self).__name__, env)
        depth += 1
        stats['func-calls'][type(self).__name__] += 1
        if isinstance(self, UfuncBase):
            for key, val in env.items():
                if val is type(self):
                    stats['ufunc-calls'][key] += 1
        rv = f(self, env)
        depth -= 1
        logger.debug(template, f'{call_indent}leave', type(self).__name__, env)
        return rv
    return inner

class Node:
    def __init__(self, *children):
        self.children = children
    def __repr__(self):
        return f'{type(self).__name__}({", ".join(repr(x) for x in self.children)})'
    def pformat(self, level=0):
        if not self.children:
            return f'{type(self).__name__}()'
        if len(self.children) == 1:
            child = self.children[0]
            child = child.pformat() if isinstance(child, Node) else repr(child)
            pfx = '\t' * level
            return indent(f'{type(self).__name__}({child})', prefix=pfx)
        sep, pfx = ',\n', '\t' * level
        children = [x.pformat(level=1) if isinstance(x, Node) else pfx + repr(x) for x in self.children]
        msg = f'{type(self).__name__}(\n{sep.join(children)}\n)'
        return indent(msg, prefix=pfx)
    def __call__(self, env):
        raise NotImplementedError()

class Comment(Node):
    @debug
    def __call__(self, env):
        return Nil

class Suite(Node):
    @debug
    def __call__(self, env):
        rv = Nil
        for child in self.children:
            rv = child(env)
        return rv

class Setq(Node):
    @debug
    def __call__(self, env):
        name, value = self.name(env), self.value(env)
        env[name.value] = value
        return value
    def __init__(self, name, value):
        super().__init__(name, value)
    name  = property(lambda self: self.children[0])
    value = property(lambda self: self.children[1])

class List(Node):
    @debug
    def __call__(self, env):
        values = [val(env) for val in self.values]
        values.reverse()
        rv = Cell(values[0], Nil)
        for v in values[1:]:
            rv = Cell(v, rv)
        return rv
    def __init__(self, car, *cdr):
        super().__init__(car, *cdr)
    values = property(lambda self: self.children)

class Cons(Node):
    @debug
    def __call__(self, env):
        car, cdr = self.car(env), self.cdr(env)
        return Cell(car, cdr)
    def __init__(self, car, cdr):
        super().__init__(car, cdr)
    car = property(lambda self: self.children[0])
    cdr = property(lambda self: self.children[1])

class Car(Node):
    @debug
    def __call__(self, env):
        return self.cons(env).car
    def __init__(self, cons):
        super().__init__(cons)
    cons = property(lambda self: self.children[0])

class Cdr(Node):
    @debug
    def __call__(self, env):
        return self.cons(env).cdr
    def __init__(self, cons):
        super().__init__(cons)
    cons = property(lambda self: self.children[0])

class Cell(Node):
    @debug
    def __call__(self, env):
        return self
    def __init__(self, car, cdr):
        super().__init__(car, cdr)
    car   = property(lambda self: self.children[0])
    cdr   = property(lambda self: self.children[1])
    value = property(lambda self: (self.car.value, self.cdr.value))

class ProgramError(Exception):
    pass

class Assert(Node):
    @debug
    def __call__(self, env):
        if not self.cond(env).value:
            raise ProgramError(self.msg(env).value)
        return Nil
    def __init__(self, cond, msg):
        super().__init__(cond, msg)
    cond = property(lambda self: self.children[0])
    msg  = property(lambda self: self.children[1])

def create_binop(name, op):
    code = dedent(f'''
    class {name}(Node):
        @debug
        def __call__(self, env):
            left, right = self.left(env), self.right(env)
            left, right = left.value, right.value   # unwrap
            return Atom({op.__name__}(left, right)) # wrap
        def __init__(self, left, right):
            super().__init__(left, right)
        left  = property(lambda self: self.children[0])
        right = property(lambda self: self.children[1])
    ''')
    ns = {}
    exec(code, globals(), ns)
    return ns[name]

def create_unop(name, op):
    code = dedent(f'''
    class {name}(Node):
        @debug
        def __call__(self, env):
            arg = self.arg(env)
            arg = arg.value   # unwrap
            return Atom({op.__name__}(arg)) # wrap
        def __init__(self, arg):
            super().__init__(arg)
        arg  = property(lambda self: self.children[0])
    ''')
    ns = {}
    exec(code, globals(), ns)
    return ns[name]

from operator import pos, neg
Pos = create_unop('Pos', pos)
Neg = create_unop('Neg', neg)

from operator import eq, ne, lt, gt, le, ge
Eq = create_binop('Eq', eq)
Ne = create_binop('Ne', ne)
Lt = create_binop('Lt', lt)
Gt = create_binop('Gt', gt)
Le = create_binop('Le', le)
Ge = create_binop('Ge', ge)

from operator import add, sub, mul, truediv, mod, pow
Add = create_binop('Add', add)
Sub = create_binop('Sub', sub)
Mul = create_binop('Mul', mul)
Div = create_binop('Div', truediv)
Mod = create_binop('Mod', mod)
Pow = create_binop('Pow', pow)

from operator import and_, or_, not_, xor, is_
And = create_binop('And', and_)
Or  = create_binop('Or',  or_)
Not = create_binop('Not', not_)
Xor = create_binop('Xor', xor)
Is  = create_binop('Is',  is_)

class Print(Node):
    @debug
    def __call__(self, env):
        args = [arg(env) for arg in self.args]
        args = [arg.value for arg in args] # unwrap
        return Atom(print(*args)) # wrap
    def __init__(self, *args):
        super().__init__(*args)
    args = property(lambda self: self.children)

class Name(Node):
    @debug
    def __call__(self, env):
        return self
    def __init__(self, name):
        super().__init__(name)
    name  = property(lambda self: self.children[0])
    value = name

class Var(Node):
    @debug
    def __call__(self, env):
        return env[self.name]
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])

class Atom(Node):
    @debug
    def __call__(self, env):
        return self
    def __init__(self, value):
        super().__init__(value)
    value = property(lambda self: self.children[0])

class Nil(Node):
    def __call__(self, env):
        return self
    value = property(lambda self: None)
Nil = Nil()

class While(Node):
    @debug
    def __call__(self, env):
        rv = Nil
        while self.cond(env).value:
            rv = self.body(env)
        return rv
    def __init__(self, cond, body):
        super().__init__(cond, body)
    cond = property(lambda self: self.children[0])
    body = property(lambda self: self.children[1])

class IfElse(Node):
    @debug
    def __call__(self, env):
        rv = Nil
        if self.cond(env).value:
            rv = self.ifbody(env)
        else:
            if self.elsebody:
                rv = self.elsebody(env)
        return rv
    def __init__(self, cond, ifbody, elsebody=None):
        super().__init__(cond, ifbody, elsebody)
    cond     = property(lambda self: self.children[0])
    ifbody   = property(lambda self: self.children[1])
    elsebody = property(lambda self: self.children[2])

class Call(Node):
    @debug
    def __call__(self, env):
        args = [arg(env) for arg in self.args]
        node = env[self.name.value](*args)
        return node(env)
    def __init__(self, name, *args):
        super().__init__(name, *args)
    name = property(lambda self: self.children[0])  
    args = property(lambda self: self.children[1:])

class UfuncBase(Node):
    pass

class Lambda(Node):
    @debug
    def __call__(self, env):
        params, body = self.params, self.body
        class Ufunc(UfuncBase):
            @debug
            def __call__(self, env):
                args = dict(zip(params.values, self.args))
                local_env = {**env, **args}
                return body(local_env)
            def __init__(self, *args):
                super().__init__(*args)
            args = property(lambda self: self.children)
        return Ufunc
    def __init__(self, params, body):
        super().__init__(params, body)
    params = property(lambda self: self.children[0])
    body   = property(lambda self: self.children[1])
