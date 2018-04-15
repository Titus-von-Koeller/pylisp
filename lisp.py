#!/usr/bin/env python3

def tokenize(expr):
    tokens = []
    string = False
    escape = False
    token = ''
    for char in expr:
        if char == '\\':
            token += char
            escape = True
        elif escape and char == '"':
            token += char
            escape = False
        elif char == '"' and not escape:
            string = not string
            token = token + char
            if not string:
                tokens.append(token)
                token = ''
        elif string: token += char
        elif char == ' ':
            if token:
                tokens.append(token)
                token = ''
        elif char in ['(', ')']:
            if token != '':
                tokens.append(token)
                token = ''
            tokens.append(char)
        else:
            token = token + char
    return tokens

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
    


def resolve(tokens):
    for value, type in tokens:
        if type == 'num':
            yield int(value), type
        elif type == 'ident' and value in ['+','-','/','*','print']:
            d = {'+' : add, '*' : mul, '-' : neg, 'print' : print}
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
    return rv[0]

def evaluate(AST):
    op, *ops = AST
    ops2 = [evaluate(o) if isinstance(o,list) else o for o in ops]
    return op(*ops2)

def test_evaluate_unary():
    s = {'(+ (* (- 3) 3) (* 4 4))' : 7,
         '(print "a" "b" "c" "d")' : None,}
    for test in s:
        r = evaluate(build_AST(resolve(tokenize2(tokenize(test)))))
        print(r, r == s[test])

def test_evaluate():
    s = {'(+ 3 (+ 4 (* 2 2)))' : 11,
         '(+ (* 3 3) (* 4 4))' : 25}
    for test in s:
        r = evaluate(build_AST(resolve(tokenize2(tokenize(test)))))
        print(r, r == s[test])

def test_build_AST():
    s = {'(+ 3 (+ 4 (* 2 2)))' : [add, 3, [add, 4, [mul, 2, 2]]],
         '(+ (* 3 3) (* 4 4))' : [add, [mul, 3, 3], [mul, 4, 4]]}
    for test in s:
        r = build_AST(resolve(tokenize2(tokenize(test))))
        print(r, r == s[test])


def test_tokenize():
    s = { '(+ 3 (+ 4 (* 2 2)))' : ['(','+','3','(','+','4','(','*','2','2',')',')',')'],
         '(+ 3000 (+ 4 (* 2 2)))' : ['(','+','3000','(','+','4','(','*','2','2',')',')',')'],
         '(list 1 2 3)' : ['(','list','1','2','3',')'],
         '("abc")' : ['(','"abc"',')'],
         '("ab cd")' : ['(','"ab cd"',')'],
         '("ab (cd)")' : ['(','"ab (cd)"',')'],
         r'("ab \"(cd)\"")' : ['(', r'"ab \"(cd)\""',')'],
         '(+ (* 3 3) (* 4 4))' : ['(','+','(','*','3','3',')','(','*','4','4',')',')'],
         }
    
    for key, value in s.items():
        if tokenize(key)!=value:
            print(key, value)
            print(tokenize(key))
            print(tokenize(key)==value)

def test_tokenize2():
    print('testing test_tokenize2:')
    s = ['(+ 3 (+ 4 (* 2)))','("abc")'] 
    for t in s:
        for token, type in tokenize2(tokenize(t)):
            print(token, type)

if __name__ == '__main__':
    test_evaluate_unary()
