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
