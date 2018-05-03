#!/usr/bin/env python3

def tokenize(expr):
    tokens = []
    string = False
    escape = False
    comment = False
    token = ''
    for char in expr:
        if char == '\\':
            token += char
            escape = True
        elif escape and char == '"':
            token += char
            escape = False
        elif char == ';' and char != string:
            token += char
            comment = True
        elif comment:
            if char != '\\n':
                token += char
            else:
                comment = False
                tokens.append(token)
                token = ''
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
        pass

    def extract_tokens(line):
        pass

                
    lines = list(filter_comments(expr))
    for string, comment, line in list(filter_strings(lines)):
        if not string:
            print(line)
            tokens = line.split('(')
            tokens = [ x for t in tokens for x in t.split(')') ]
            tokens = [ x for t in tokens for x in t.split(' ') ]
            print(tokens)


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
        if r != s[test]:
            print(f'FAILURE: {r} != {s[test]}')

def test_evaluate():
    s = {'(+ 3 (+ 4 (* 2 2)))' : 11,
         '(+ (* 3 3) (* 4 4))' : 25}
    for test in s:
        r = evaluate(build_AST(resolve(tokenize2(tokenize(test)))))
        if r != s[test]:
            print(f'FAILURE: {r} != {s[test]}')

def test_build_AST():
    s = {'(+ 3 (+ 4 (* 2 2)))' : [add, 3, [add, 4, [mul, 2, 2]]],
         '(+ (* 3 3) (* 4 4))' : [add, [mul, 3, 3], [mul, 4, 4]]}
    for test in s:
        r = build_AST(resolve(tokenize2(tokenize(test))))
        if r != s[test]:
            print(f'FAILURE: {r} != {s[test]}')
            


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
    
    run_on_dict(s, tokenize)

def test_tokenize2():
    s = {'(+ 3 (+ 4 (* 2)))' : [('(','openp'), ('+','ident'), ('3','num'), 
                                ('(','openp'), ('+','ident'), ('4','num'), 
                                ('(','openp'), ('*','ident'), ('2','num'), 
                                (')','closep'),(')', 'closep'), (')','closep')],
         '("abc")' : [('(', 'openp'), ('"abc"', 'str'), (')', 'closep')] }
    run_on_dict(s, tokenize, tokenize2, list)

def run_on_dict(d, *pipeline):
    for key, value in d.items():
        r = key
        for func in pipeline:
            r = func(r)
            print(f'calling {func.__name__}')
        if r != value:
            print(f'FAILURE :  {r}  !=  {value}')
            break
    else:
        print("SUCCESS :  all tests passed!")

if __name__ == '__main__':
    from sys import argv
    fn = argv[1]
    with open(fn) as f:
        contents = f.read()
    print(tokenize(contents))
    # test_tokenize()
    # test_tokenize2()
    # test_evaluate_unary()
    # test_build_AST()
    s = ['(+ 3 (+ 4 (* 2)))','("abc")'] 
    # [tokens] : [(token,type)] 
    d = dict()
    # for t in s:
    #     for token, type in tokenize2(tokenize(t)):
    #         token, type)
