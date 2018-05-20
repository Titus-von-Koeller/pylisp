#!/usr/bin/env python3
from nodes import *
from random import randint
from argparse import ArgumentParser
from logging import getLogger, basicConfig, DEBUG, INFO, ERROR
logger = getLogger(__name__)

def test_cons():
    return Suite(
        Comment('(cons 1 (cons 2 (cons 3 nil)))'),
        Setq(
            Name('x'),
            Cons(Atom(1), Cons(Atom(2), Cons(Atom(3), Nil))),
        ),
        Setq(
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
        Setq(
            Name('x'),
            Atom(x),
        ),
        Setq(
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

def test_controlflow():
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
    return Suite(
        Setq(
            Name('x'),
            Atom(0),
        ),
        Setq(
            Name('n'),
            Atom(20),
        ),
        Setq(
            Name('rv'),
            Nil,
        ),
        While(
            Lt(Var('x'), Var('n')),
            Suite(
                Setq(
                    Name('x'),
                    Add(Var('x'), Atom(1))
                ),
                IfElse(
                    Eq(
                        Mod(Var('x'), Atom(15)),
                        Atom(0),
                    ),
                    Setq(
                        Name('rv'),
                        Cons(Atom('fizzbuzz'), Var('rv')),
                    ),
                    IfElse(
                        Eq(
                            Mod(Var('x'), Atom(5)),
                            Atom(0),
                        ),
                        Setq(
                            Name('rv'),
                            Cons(Atom('buzz'), Var('rv')),
                        ),
                        IfElse(
                            Eq(
                                Mod(Var('x'), Atom(3)),
                                Atom(0),
                            ),
                            Setq(
                                Name('rv'),
                                Cons(Atom('fizz'), Var('rv')),
                            ),
                            Setq(
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
        Setq(
            Name('fib'),
            Lambda(
                List('n'),
                Suite(
                    IfElse(
                        Or(
                            Eq(Var('n'), Atom(0)),
                            Eq(Var('n'), Atom(1)),
                        ),
                        Atom(1),
                        Suite(
                            Setq(
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
        Setq(
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
        Print(Atom('All tests passed!')),
    )

parser = ArgumentParser()
parser.add_argument('-v', '--verbose', action='count')
parser.add_argument('-s', '--stats', action='store_true', default=False)
parser.add_argument('tests', nargs='+')

if __name__ == '__main__':
    args = parser.parse_args()
    basicConfig(level={2: DEBUG, 1: INFO}.get(args.verbose, ERROR))

    if 'cons' in args.tests:
        suite = test_cons()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'arithmetic' in args.tests:
        suite = test_arithmetic(randint(1, 100), randint(1, 100))
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'controlflow' in args.tests:
        suite = test_controlflow()
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if 'functions' in args.tests:
        suite = test_functions(10)
        logger.info(f'suite = %s',           suite.pformat())
        logger.info(f'suite(env={{}}) = %r', suite(env={}))

    if args.stats:
        print_stats()
