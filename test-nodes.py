#!/usr/bin/env python3
from nodes import *
from random import randint
from argparse import ArgumentParser
from logging import getLogger, basicConfig, DEBUG, INFO, ERROR
logger = getLogger(__name__)

def test_cons():
    return Suite(
        Comment('(cons 1 (cons 2 (cons 3 nil)))'),
        Set(
            Name('x'),
            Cons(Atom(1), Cons(Atom(2), Cons(Atom(3), Nil))),
        ),
        Set(
            Name('y'),
            List(Atom(1), Atom(2), Atom(3)),
        ),
        Assert(
            Eq(
                Car(Var('x')),
                Atom(1),
            ),
            Atom('(car x) failed'),
        ),
        Assert(
            Eq(
                Car(Cdr(Var('x'))),
                Atom(2),
            ),
            Atom('(car (cdr x)) failed'),
        ),
        Assert(
            Eq(
                Car(Cdr(Cdr(Var('x')))),
                Atom(3),
            ),
            Atom('(car (cdr (cdr x))) failed'),
        ),
        Assert(
            Eq(Var('x'), Var('y')),
            Atom('(eq x y) failed'),
        ),
        Print(
            Atom('All cons/car/cdr tests passed!')
        ),
    )

def test_arithmetic(x, y):
    return Suite(
        Comment(f'x = {x}, y = {y}'),
        Set(
            Name('x'),
            Atom(x),
        ),
        Set(
            Name('y'),
            Atom(y),
        ),
        Assert(
            Eq(
                Neg(
                    Div(
                        Mul(
                            Var('x'),
                            Sub(Atom(4), Atom(2)),
                        ),
                        Mul(
                            Var('y'),
                            Add(Atom(1), Atom(1)),
                        ),
                    ),
                ),
                Atom( - (x * (4 - 2)) / (y * (1 + 1))  ),
            ),
            Atom('(- (/ (* x (- 4 2)) (* y (+ 1 1)))) failed'),
        ),
        Print(
            Atom('All arithmetic tests passed!')
        ),
    )

def fizzbuzz(n):
    for x in range(n, 0, -1):
        if x % 15 == 0:
            yield 'fizzbuzz'
        elif x % 5 == 0:
            yield 'buzz'
        elif x % 3 == 0:
            yield 'fizz'
        else:
            yield x

def test_controlflow():
    return Suite(
        Set(
            Name('x'),
            Atom(0),
        ),
        Set(
            Name('n'),
            Atom(20),
        ),
        Set(
            Name('rv'),
            Nil,
        ),
        While(
            Lt(Var('x'), Var('n')),
            Suite(
                Set(
                    Name('x'),
                    Add(Var('x'), Atom(1))
                ),
                IfElse(
                    Eq(
                        Mod(Var('x'), Atom(15)),
                        Atom(0),
                    ),
                    Set(
                        Name('rv'),
                        Cons(Atom('fizzbuzz'), Var('rv')),
                    ),
                    IfElse(
                        Eq(
                            Mod(Var('x'), Atom(5)),
                            Atom(0),
                        ),
                        Set(
                            Name('rv'),
                            Cons(Atom('buzz'), Var('rv')),
                        ),
                        IfElse(
                            Eq(
                                Mod(Var('x'), Atom(3)),
                                Atom(0),
                            ),
                            Set(
                                Name('rv'),
                                Cons(Atom('fizz'), Var('rv')),
                            ),
                            Set(
                                Name('rv'),
                                Cons(Var('x'), Var('rv')),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        Assert(
            Eq(
                Var('rv'),
                List( *[Atom(x) for x in fizzbuzz(20)] ),
            ),
            Atom('(fizzbuzz 20) failed!')
        ),
        Print(
            Atom('All control flow tests passed!')
        ),
    )

def test_functions(n):
    def fib(n):
        if n == 0 or n == 1:
            return 1
        return fib(n-1) + fib(n-2)
    return Suite(
        Set(
            Name('fib'),
            Lambda(
                Params('n'),
                Suite(
                    IfElse(
                        Or(
                            Eq(Var('n'), Atom(0)),
                            Eq(Var('n'), Atom(1)),
                        ),
                        Atom(1),
                        Suite(
                            Set(
                                Name('rv'),
                                Add(
                                    Call(
                                        Name('fib'),
                                        Sub(Var('n'), Atom(1)),
                                    ),
                                    Call(
                                        Name('fib'),
                                        Sub(Var('n'), Atom(2)),
                                    ),
                                ),
                            ),
                            Var('rv'),
                        ),
                    ),
                ),
            ),
        ),
        Set(
            Name('rv'),
            Call(
                Name('fib'),
                Atom(n),
            ),
        ),
        Print(Atom(f'(fib {n}) ='), Var('rv')),
        Assert(
            Eq(
                Var('rv'),
                Atom(fib(n)),
            ),
            Atom(f'(fib {n}) failed!'),
        ),
        Print(Atom('All functions tests passed!')),
    )

def test_tco(n):
    def fact(n):
        if n == 0:
            return 1
        return n * fact(n-1)
    return Suite(
        Set(
            Name('fact'),
            Lambda(
                Params('n'),
                Suite(
                    IfElse(
                        Eq(
                            Var('n'),
                            Atom(0),
                        ),
                        Atom(1),
                        Mul(
                            Var('n'),
                            Call(
                                Name('fact'),
                                Sub(Var('n'), Atom(1)),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        Set(
            Name('rv'),
            Call(
                Name('fact'),
                Atom(n),
            ),
        ),
        Print(
            Atom(f'(fact {n}) ='),
            Var('rv'),
        ),
        Assert(
            Eq(
                Var('rv'),
                Atom(fact(n)),
            ),
            Atom(f'(fact {n}) failed!')
        ),
        Print(Atom('All tests passed!')),
    )

def test_parser():
    def quote(x):
        if isinstance(x, str):
            return f'"{x}"'
        return repr(x)
    code = f'''
    (set print-list (lambda (xs) (
        (while (<> xs nil)
            (printf "{{}} " (car xs))
            (set xs (cdr xs))
        )
        (printf "\n")
    )))

    (
        (print "simple test")
        (set add (lambda (x y) (+ x y)))
        (print "1 + 2 =" (add 1 2))
        (assert (== (add 1 2) 3) "add 1 2) failed!")
        (print "All tests passed!")
    )
    (
        (print "hard test")
        (set fizzbuzz (
            lambda (x) (
                (set n 0)
                (set rv nil)
                (while (< n x)
                    (set n (+ n 1))
                    (if (== (% n 15) 0)
                        (set rv (cons "fizzbuzz" rv))
                        (if (== (% n 5) 0)
                            (set rv (cons "buzz" rv))
                            (if (== (% n 3) 0)
                                (set rv (cons "fizz" rv))
                                (set rv (cons n rv))
                            )
                        )
                    )
                )
                (get rv)
            )
        ))
        (print-list (cons "(fizzbuzz 20) =" (fizzbuzz 20)))
        (assert
            (==
                (fizzbuzz 20)
                (list {" ".join(quote(x) for x in fizzbuzz(20))})
            )
            "(fizzbuzz 20) failed!"
        )

        (print "All tests passed!")
    )
    '''
    return parse(code)

def test_repl():
    code = '''
    (print (parse "(+ 1 2)"))

    (set node '(+ 1 2))
    (print "<" (eval node) ">")

    (set name (read))
    (printf "hello, {}\n" name)

    (set line nil)
    (while (<> line "") (
        (set line (read))
        (set code (parse line))
        (printf ">>> {}\n" line)
        (print (eval code))
    ))
    '''
    return parse(code)

def test_scoping():
    code = '''
        (set y 10)
        (set z 10)

        (set create-closure-fun (lambda (z) (
            (set closure-fun (lambda () (
                (get z)
            )))
        )))

        (set fun1 (create-closure-fun 10))
        (set fun2 (create-closure-fun 100))
        (printf "(fun1) = {}\n" (fun1))
        (printf "(fun2) = {}\n" (fun2))

        (assert (== 10  (fun1)) "(fun1) failed!")
        (assert (== 100 (fun2)) "(fun1) failed!")

        (set create-nested-closure-fun (lambda (z) (
            (set create-closure-fun (lambda () (
                (set closure-fun (lambda () (
                    (get z)
                )))
            )))
            (create-closure-fun)
        )))

        (set fun1 (create-nested-closure-fun 10))
        (set fun2 (create-nested-closure-fun 100))
        (printf "(fun1) = {}\n" (fun1))
        (printf "(fun2) = {}\n" (fun2))

        (assert (== 10  (fun1)) "(fun1) failed!")
        (assert (== 100 (fun2)) "(fun1) failed!")

        (set f (lambda (x) (
            (printf "inside f - before - x = {:5f}, y = {:5f}\n" x y)
            (assert (and (== x 10) (== y 10)) "Scoping failed!")
            (set x 100)
            (setg y 100)
            (printf "inside f - after  - x = {:5f}, y = {:5f}\n" x y)
            (assert (and (== x 100) (== y 100)) "Scoping failed!")
        )))

        (set h (lambda (x) (
            (set y (* y 10))
            (g x)
        )))

        (set g (lambda (x) (
            (printf "inside g - before - x = {:5f}, y = {:5f}\n" x y)
            (assert (and (== x 100) (== y 100)) "Scoping failed!")
            (set x 1000)
            (set y 1000)
            (printf "inside g - after  - x = {:5f}, y = {:5f}\n" x y)
            (assert (and (== x 1000) (== y 1000)) "Scoping failed!")
        )))

        (set x 10)
        (printf "outside  - before - x = {:5f}, y = {:5f}\n" x y)
        (assert (and (== x 10) (== y 10)) "Scoping failed!")
        (f x)
        (printf "outside  - after  - x = {:5f}, y = {:5f}\n" x y)
        (assert (and (== x 10) (== y 100)) "Scoping failed!")

        (print "All scoping tests passed!")
    '''
    return parse(code)

def test_bytecode():
    code = '''
        (print "Bytecode test.")
        (set x (+ 1 1))
        (set x (* x 10))
        (printf "x = {}" x)
    '''
    return parse(code)

def test_eval():
    insts = [
        # x = 0
        PushImm(Atom(0)),
        PopVar('x'),

        # while x < 3:
        Label('loop-start'),
        PushVar('x'),
        PushImm(Atom(3)),
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

    func_insts = [
        # print('inside', 'before', x)
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
        # print('outside', 'before', x)
        PushVar('x'),
        PushImm(Atom('before')),
        PushImm(Atom('outside')),
        CallPyFunc(print, 3),
        # f(x * 10)
        PushImm(Atom(10)),
        PushVar('x'),
        CallPyFunc(mul, 2),
        PushFunc(func_insts, ['x']),
        # print('outside', 'after', x)
        PushVar('x'),
        PushImm(Atom('after')),
        PushImm(Atom('outside')),
        CallPyFunc(print, 3),
        Halt(),
    ]
    eval(insts)

parser = ArgumentParser()
parser.add_argument('-v', '--verbose', action='count')
parser.add_argument('-s', '--stats', action='store_true', default=False)
parser.add_argument('tests', nargs='*')

if __name__ == '__main__':
    args = parser.parse_args()
    basicConfig(level={2: DEBUG, 1: INFO}.get(args.verbose, ERROR))

    if 'cons' in args.tests or not args.tests:
        suite = test_cons()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'arithmetic' in args.tests or not args.tests:
        suite = test_arithmetic(randint(1, 100), randint(1, 100))
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'controlflow' in args.tests or not args.tests:
        suite = test_controlflow()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'functions' in args.tests or not args.tests:
        suite = test_functions(10)
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'tco' in args.tests:
        suite = test_tco(40)
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'parser' in args.tests or not args.tests:
        suite = test_parser()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    def mock_stdin():
        yield 'Bob'
        yield '(+ 1 2)'
        yield '(set x (+ 1 2))'
        yield '(* x 10)'
        yield ''
    MockStdin = create_pyfunc('MockStdin', mock_stdin().__next__)

    if 'repl' in args.tests or not args.tests:
        suite = test_repl()
        logger.info(f'suite = %s', suite.pformat())
        env = {'--stdin': MockStdin()}
        logger.info(f'suite(env=%r) = %r', env, suite(env=env))

    import nodes
    # nodes.__scoping__ = nodes.Scoping.DYNAMIC
    if 'scoping' in args.tests or not args.tests:
        suite = test_scoping()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'bytecode' in args.tests or not args.tests:
        suite = test_bytecode()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info('iter(suite):\n%s', '\n'.join('\t' + repr(x) for x in suite))
        logger.info('eval(suite, env={}) = %r', eval(suite, env={}))

    if 'eval' in args.tests or not args.tests:
        test_eval()

    print('All tests passed!')

    if args.stats:
        print_stats()
