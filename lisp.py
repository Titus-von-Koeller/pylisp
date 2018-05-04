#!/usr/bin/env python3

from re import split

def tokenize(expr):
    # filter out comments
    def filter_comments(expr):
        for line in expr.splitlines():
            line = line.lstrip(" ")
            if line.startswith(";"):
                yield True, line
            else:
                yield False, line

    # filter strings
    def filter_strings(lines):
        for comment, line in lines:
            if comment:
                yield False, comment, line
            elif '"' in line:
                yield True, comment, line
            else:
                yield False, comment, line

    def extract_string(line):
       return split('("[^"]*")', line)


    def extract_tokens(line):
        return [ x for x in split('([ \(\)])', line) if x.strip() ]

    lines = list(filter_comments(expr))

    for string, comment, line in list(filter_strings(lines)):
        if comment:
            pass
        elif string:
            for part in extract_string(line):
                if part.startswith('"'):
                    yield part
                else:
                    yield from extract_tokens(part)
        else:
            yield from extract_tokens(line)



    # filter out pairs of parenths

def tokenize2(expr):
    for token in expr:
        if token == '(': 
            yield token, 'openp' 
        elif token == ')':
            yield token, 'closep' 
        elif token.startswith('"'):
            yield token, 'str'
        elif token[0].isdigit():
            yield token, 'num'
        else:
            yield token, 'ident'

def fix_strings():
    pass

from operator import add, mul
def neg(op1, op2=None):
    if op2 == None:
        return -op1
    return op1 - op2
def _import(*ops):
    print(f'importing {ops[1:]}')


def resolve(tokens):
    for value, type in tokens:
        value = value.strip()
        if type == 'num':
            yield int(value), type
        elif type == 'ident' and value in ['+','-','/','*','print', 
                                           'display', 'import', 'newline',
                                           'scheme']:
            d = {'+' : add, '*' : mul, '-' : neg, 'print' : print,
                 'display': print, 'import': _import, 'newline': print,
                 'scheme': print, }
            yield d[value], type
        else:
            yield value, type


def build_AST(tokens):
    rv = []
    current = [rv]
    for value, type in tokens:
        if type == 'openp':
            t = []
            current[-1].append(t)
            current.append(t)
        elif type == 'closep':
            current.pop()
        else:
            current[-1].append(value)
    return rv

def evaluate(AST):
    if all(isinstance(o, list) for o in AST):
        return [evaluate(o) for o in AST]
    op, *ops = AST
    try:
        ops2 = [evaluate(o) if isinstance(o,list) else o for o in ops]
    except Exception as e:
        raise ValueError(op) from e
    return op(*ops2)

if __name__ == '__main__':
    from sys import argv
    fn = argv[1]
    with open(fn) as f:
        contents = f.read()
    AST = build_AST(resolve(tokenize2(tokenize(contents))))
    print(list(evaluate(AST)))
