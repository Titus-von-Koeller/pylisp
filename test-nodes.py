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

    if args.stats:
        print_stats()
