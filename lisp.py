#!/usr/bin/env python3

def tokenize(expr):
    tokens = []
    string = False
    escape = False
    token = ''
    for char in expr:
        print(char, token)   
        if char == '\\':
            token += char
            escape = True
        elif escape and char == '"':
            token += char
            escape = False
        elif char == '"' and not escape:
            string = not string
            token = token + char
            print(string)
            if not string:
                tokens.append(token)
                token = ''
        elif string: token += char
        elif char == ' ':
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

if __name__ == '__main__':
    s = { '(+ 3 (+ 4 (* 2)))' : ['(','+','3','(','+','4','(','*','2',')',')',')'],
         '(+ 3000 (+ 4 (* 2)))' : ['(','+','3000','(','+','4','(','*','2',')',')',')'],
         '(list 1 2 3)' : ['(','list','1','2','3',')'],
         '("abc")' : ['(','"abc"',')'],
         '("ab cd")' : ['(','"ab cd"',')'],
         '("ab (cd)")' : ['(','"ab (cd)"',')'],
         r'("ab \"(cd)\"")' : ['(', '"ab \"(cd)\"")'],
         }
    
    for r in [s[-1]]:
        print(r)
        print(tokenize(r))

