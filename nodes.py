#!/usr/bin/env python3
from re import compile, escape
from decimal import Decimal
from textwrap import indent, dedent
from collections import defaultdict, Iterable, ChainMap
from functools import wraps
from logging import getLogger
from pprint import pformat
from enum import Enum, auto
from sys import stdin
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
    def __iter__(self):
        yield Missing(self)
    @classmethod
    def parse(cls, tree):
        NUM_RE = compile(r'(?:\+|-)?\d*\.?\d*')
        if not isinstance(tree, list):
            if NUM_RE.fullmatch(tree):
                return Atom(Decimal(tree))
            if tree.startswith('"') and tree.endswith('"'):
                return Atom(tree[1:-1])
            if tree == 'nil':
                return Nil
            if tree == 'true':
                return True_
            return Var(tree)
            if tree == 'false':
                return False_
        if all(isinstance(x, list) for x in tree):
            return Suite.parse(tree)
        if tree[0] == 'set':
            return Set.parse(tree)
        if tree[0] == 'setg':
            return Setg.parse(tree)
        if tree[0] == 'setc':
            return Setc.parse(tree)
        if tree[0] == 'get':
            return Get.parse(tree)
        if tree[0] == 'lambda':
            return Lambda.parse(tree)
        comparisons = {'==': Eq, '<>': Ne, '<': Lt, '>': Gt, '<=': Le, '>=': Ge,}
        if tree[0] in comparisons:
            return comparisons[tree[0]].parse(tree)
        ops = {'+': {1: Pos, 2: Add},
               '-': {1: Neg, 2: Sub},
               '*': {2: Mul}, '/': {2: Div}, '%': {2: Mod}, '**': {2: Pow},
               'and': {2: And}, 'or': {2: Or}, 'not': {1: Not}, 'xor': {2: Xor}}
        if tree[0] in ops:
            return ops[tree[0]][len(tree[1:])].parse(tree)
        pyfuncs = {'print': Print, 'printf': Printf, 'printfs': Printfs}
        if tree[0] in pyfuncs:
            return pyfuncs[tree[0]].parse(tree)
        if tree[0] == 'assert':
            return Assert.parse(tree)
        if tree[0] == 'list':
            return List.parse(tree)
        if tree[0] == 'cons':
            return Cons.parse(tree)
        if tree[0] == 'car':
            return Car.parse(tree)
        if tree[0] == 'cdr':
            return Cdr.parse(tree)
        if tree[0] == 'if':
            return IfElse.parse(tree)
        if tree[0] == 'while':
            return While.parse(tree)
        if tree[0] == 'parse':
            return Parse.parse(tree)
        if tree[0] == 'quoted':
            return Atom(Node.parse(tree[1]))
        if tree[0] == 'eval':
            return Eval.parse(tree)
        if tree[0] == 'read':
            return Read.parse(tree)
        if len(tree) == 1:
            return Call.parse(tree)
        if isinstance(tree[0], str):
            if len(tree) > 1:
                return Call.parse(tree)
            return Var(tree[0])
        return NotImplemented.parse(tree)

class NotImplemented(Node):
    @classmethod
    def parse(cls, tree):
        return cls(tree)

class Comment(Node):
    @debug
    def __call__(self, env):
        return Nil
    def __iter__(self):
        yield Noop()

class Suite(Node):
    @debug
    def __call__(self, env):
        rv = Nil
        for child in self.children:
            rv = child(env)
        return rv
    @classmethod
    def parse(self, tree):
        return Suite(*[Node.parse(element) for element in tree])
    def __iter__(self):
        for child in self.children:
            yield from child

class Set(Node):
    @debug
    def __call__(self, env):
        name, value = self.name(env), self.value(env)
        env[name.value] = value
        return value
    def __init__(self, name, value):
        super().__init__(name, value)
    name  = property(lambda self: self.children[0])
    value = property(lambda self: self.children[1])
    @classmethod
    def parse(cls, tree):
        _, name, value = tree
        return cls(Name(name), Node.parse(value))

class Setg(Node):
    @debug
    def __call__(self, env):
        name, value = self.name(env), self.value(env)
        if isinstance(env, ChainMap):
            env.maps[-1][name.value] = value
        else:
            env[name.value] = value
        return value
    def __init__(self, name, value):
        super().__init__(name, value)
    name  = property(lambda self: self.children[0])
    value = property(lambda self: self.children[1])
    @classmethod
    def parse(cls, tree):
        _, name, value = tree
        return cls(Name(name), Node.parse(value))

class Setc(Node):
    @debug
    def __call__(self, env):
        name, value = self.name(env), self.value(env)
        if isinstance(env, ChainMap):
            env.maps[1][name.value] = value
        else:
            env[name.value] = value
        return value
    def __init__(self, name, value):
        super().__init__(name, value)
    name  = property(lambda self: self.children[0])
    value = property(lambda self: self.children[1])
    @classmethod
    def parse(cls, tree):
        _, name, value = tree
        return cls(Name(name), Node.parse(value))

class Get(Node):
    @debug
    def __call__(self, env):
        return env[self.name.value]
    def __init__(self, name):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    @classmethod
    def parse(cls, tree):
        _, name = tree
        return cls(Name(name))

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
    @classmethod
    def parse(cls, tree):
        _, *tree = tree
        return cls(*[Node.parse(x) for x in tree])

class Params(Node):
    def __call__(self, env):
        return self
    def __init__(self, *params):
       super().__init__(*params)
    params = property(lambda self: self.children)
    value  = property(lambda self: self.params)
    @classmethod
    def parse(cls, tree):
        return cls(*tree)

class Cons(Node):
    @debug
    def __call__(self, env):
        car, cdr = self.car(env), self.cdr(env)
        return Cell(car, cdr)
    def __init__(self, car, cdr):
        super().__init__(car, cdr)
    car = property(lambda self: self.children[0])
    cdr = property(lambda self: self.children[1])
    @classmethod
    def parse(cls, tree):
        _, car, cdr = tree
        return cls(Node.parse(car), Node.parse(cdr))

class Car(Node):
    @debug
    def __call__(self, env):
        return self.cons(env).car
    def __init__(self, cons):
        super().__init__(cons)
    cons = property(lambda self: self.children[0])
    @classmethod
    def parse(cls, tree):
        _, cons = tree
        return cls(Node.parse(cons))

class Cdr(Node):
    @debug
    def __call__(self, env):
        return self.cons(env).cdr
    def __init__(self, cons):
        super().__init__(cons)
    cons = property(lambda self: self.children[0])
    @classmethod
    def parse(cls, tree):
        _, cons = tree
        return cls(Node.parse(cons))

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
    @classmethod
    def parse(cls, tree):
        _, cond, msg = tree
        return cls(Node.parse(cond), Node.parse(msg))

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
        @classmethod
        def parse(cls, tree):
            _, left, right = tree
            return cls(Node.parse(left), Node.parse(right))
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
        @classmethod
        def parse(cls, tree):
            _, arg = tree
            return cls(Node.parse(arg))
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

def create_pyfunc(name, func):
    code = dedent(f'''
    def create_func(func):
        class {name}(Node):
            @debug
            def __call__(self, env):
                args = [arg(env) for arg in self.args]
                args = [arg.value for arg in args] # unwrap
                rv = func(*args)
                return Atom(rv) # wrap
            def __init__(self, *args):
                super().__init__(*args)
            args = property(lambda self: self.children)
            @classmethod
            def parse(cls, tree):
                _, *args = tree
                return cls(*[Node.parse(x) for x in args])
            def __iter__(self):
                yield CallPyFunc(func, *self.args)
        return {name}
    ''')
    ns = {}
    exec(code, globals(), ns)
    return ns['create_func'](func)

def printf(fmt, *args):
    return print(fmt.format(*args), end='')

def printfs(fmt, sep, *args):
    return print(fmt.format(*args), sep=sep, end='')

Print   = create_pyfunc('Print', print)
Printf  = create_pyfunc('Printf', printf)
Printfs = create_pyfunc('Printfs', printfs)

class Name(Node):
    @debug
    def __call__(self, env):
        return self
    def __init__(self, name):
        super().__init__(name)
    name  = property(lambda self: self.children[0])
    value = name
    @classmethod
    def parse(cls, tree):
        name = tree[0] if isinstance(tree, list) else tree
        return Name(name)

class Var(Node):
    @debug
    def __call__(self, env):
        try:
            return env[self.name](env)
        except KeyError as e:
            raise ProgramError(f'unknown name {self.name!r}') from e
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

class True_(Node):
    def __call__(self, env):
        return self
    value = property(lambda self: True)
True_ = True_()

class False_(Node):
    def __call__(self, env):
        return self
    value = property(lambda self: False)
False_ = False_()

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
    @classmethod
    def parse(cls, tree):
        _, cond, *body = tree
        if len(body) > 1:
            return cls(Node.parse(cond), Suite.parse(body))
        return cls(Node.parse(cond), Node.parse(*body))

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
    @classmethod
    def parse(cls, tree):
        _, cond, ifbody, *elsebody = tree
        if elsebody:
            return cls(Node.parse(cond), Node.parse(ifbody), Node.parse(*elsebody))
        return cls(Node.parse(cond), Node.parse(ifbody))

class Call(Node):
    @debug
    def __call__(self, env):
        args = [arg(env) for arg in self.args]
        try:
            node = env[self.name.value](*args)
        except KeyError as e:
            raise ProgramError(f'unknown name {self.name.value!r}') from e
        return node(env)
    def __init__(self, name, *args):
        super().__init__(name, *args)
    name = property(lambda self: self.children[0])
    args = property(lambda self: self.children[1:])
    @classmethod
    def parse(cls, tree):
        name, *args = tree
        return cls(Name(name), *[Node.parse(x) for x in args])

class UfuncBase(Node):
    pass

class Scoping(Enum):
    DYNAMIC = auto()
    LEXICAL = auto()

__scoping__ = Scoping.LEXICAL

class Lambda(Node):
    @debug
    def __call__(self, env):
        params, body = self.params, self.body
        if isinstance(env, ChainMap):
            closures = env.maps[:-1]
        else:
            closures = []
        class Ufunc(UfuncBase):
            @debug
            def __call__(self, env):
                args = dict(zip(params.value, self.args))
                if isinstance(env, ChainMap) and __scoping__ is Scoping.LEXICAL:
                    local_env = ChainMap(args, *closures, env.maps[-1])
                else:
                    local_env = ChainMap(args, *closures, env)
                return body(local_env)
            def __init__(self, *args):
                super().__init__(*args)
            args  = property(lambda self: self.children)
            value = property(lambda self: self)
        return Ufunc
    def __init__(self, params, body):
        super().__init__(params, body)
    params = property(lambda self: self.children[0])
    body   = property(lambda self: self.children[1])
    @classmethod
    def parse(cls, tree):
        _, params, body = tree
        return cls(Params.parse(params), Node.parse(body))

class Read(Node):
    @debug
    def __call__(self, env):
        if '--stdin' in env:
            return env['--stdin'](env)
        line = next(stdin)
        return Atom(line)
    def __init__(self):
        super().__init__()
    @classmethod
    def parse(cls, tree):
        return cls()

class Parse(Node):
    @debug
    def __call__(self, env):
        expr = self.expr
        code = expr(env).value
        node = parse(code)
        return Atom(node)
    def __init__(self, expr):
        super().__init__(expr)
    expr = property(lambda self: self.children[0])
    @classmethod
    def parse(cls, tree):
        _, expr = tree
        return cls(Node.parse(expr))

class Eval(Node):
    @debug
    def __call__(self, env):
        expr = self.expr
        node = expr(env).value
        return node(env)
    def __init__(self, expr):
        super().__init__(expr)
    expr = property(lambda self: self.children[0])
    @classmethod
    def parse(cls, tree):
        _, expr = tree
        return cls(Node.parse(expr))

class Inst:
    def __init__(self, *children):
        self.children = children
    def __repr__(self):
        return f'{type(self).__name__}({", ".join(repr(x) for x in self.children)})'

class Noop(Inst):
    def __call__(self):
        pass

class Missing(Inst):
    def __init__(self, node):
        super().__init__(node)

class CallPyFunc(Inst):
    def __init__(self, func, args):
        super().__init__(func, args)
    func = property(lambda self: self.children[0])
    args = property(lambda self: self.children[1])
    def __call__(self, frames):
        args = [frames[-1].pop() for _ in range(self.args)]
        args = [arg.value for arg in args] # unwrap
        rv = self.func(*args)
        rv = Atom(rv) # wrap
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
        if val.value:
            frames[-1].jump(self.label)

class PushFunc(Inst):
    def __init__(self, insts, names=(), pc=0, stack=None, env=None):
        super().__init__(insts, names, pc, stack, env)
    insts = property(lambda self: self.children[0])
    names = property(lambda self: self.children[1])
    pc    = property(lambda self: self.children[2])
    stack = property(lambda self: self.children[3])
    env   = property(lambda self: self.children[4])
    def __call__(self, frames):
        local_env = {}
        for n in self.names:
            local_env[n] = frames[-1].pop()
        outside_env = frames[-1].env
        if isinstance(outside_env, ChainMap):
            env = ChainMap(self.env or {}, local_env, outside_env.maps[-1])
        else:
            env = ChainMap(self.env or {}, local_env, outside_env)
        frame = Frame(self.insts, self.pc, self.stack, env)
        frames.append(frame)

class PopFunc(Inst):
    def __init__(self, name=None):
        super().__init__(name)
    name = property(lambda self: self.children[0])
    def __call__(self, frames):
        if self.name is not None:
            rv = frames[-1].env[self.name]
        else:
            rv = Nil
        frames.pop()
        if frames: frames[-1].push(rv)

class Frame:
    def __init__(self, insts, pc=0, stack=None, env=None):
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
    def __iter__(self):
        self.pc = 0
        return self
    def __next__(self):
        if self.pc is None or not (0 <= self.pc < len(self.insts)):
            raise StopIteration()
        inst = self.insts[self.pc]
        self.pc += 1
        return inst
    def push(self, value):
        self.stack.append(value)
    def pop(self):
        return self.stack.pop()
    def jump(self, label):
        self.pc = self.labels[label]

def eval(insts, env=None):
    if env is None:
        env = {}

    frames = [Frame(insts, env=env)]
    while frames:
        try:
            inst = next(frames[-1])
        except StopIteration:
            break
        inst(frames)

func_insts = [
    # print('outisde', 'before', x)
    PushVar('x'),
    PushImm(Atom('before')),
    PushImm(Atom('inside')),
    CallPyFunc(print, 3),
    # x = x * 10
    PushVar('x'),
    PushImm(Atom(10)),
    CallPyFunc(mul, 2),
    PopVar('x'),
    # print('inside', 'after', x)
    PushVar('x'),
    PushImm(Atom('after')),
    PushImm(Atom('inside')),
    CallPyFunc(print, 3),
    PopFunc(),
]

insts = [
    # x = 0
    PushImm(Atom(1)),
    PopVar('x'),
    # print('outisde', 'before', x)
    PushVar('x'),
    PushImm(Atom('before')),
    PushImm(Atom('outside')),
    CallPyFunc(print, 3),
    # f(x * 10)
    PushImm(Atom(10)),
    PushVar('x'),
    CallPyFunc(mul, 2),
    PushFunc(func_insts, ['x']),
    # print('inside', 'after', x)
    PushVar('x'),
    PushImm(Atom('after')),
    PushImm(Atom('outside')),
    CallPyFunc(print, 3),
]
[
    # x = 0
    PushImm(Atom(0)),
    PopVar('x'), 

    # while x < -1:
    Label('loop-start'),
    PushVar('x'),
    PushImm(Atom(10)),
    CallPyFunc(lt, 2),
    JumpIfTrue('loop-end'),

    # print('x =', x)
    PushVar('x'),
    PushImm(Atom('x =')),
    CallPyFunc(print, 2),

    PushImm(Atom("hello world")),
    CallPyFunc(print, 1),
    PushImm(Atom(1)),
    PushImm(Atom(1)),
    CallPyFunc(add, 2),
    PushVar('msg'),
    CallPyFunc(print, 2),

    # x = x + 1
    PushVar('x'),
    PushImm(Atom(1)),
    CallPyFunc(add, 2),
    PopVar('x'),
    JumpAlways('loop-start'),
    Label('loop-end'),

    Halt(),
    PushImm(Atom("goodbye")),
    CallPyFunc(print, 1),
]
eval(insts, {'msg': Atom('1 + 1 =')})

from sys import exit; exit()

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
