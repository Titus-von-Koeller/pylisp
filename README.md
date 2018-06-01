# Intro
This is a parser and byte-code interpreter for a Lisp-like language, implemented in Python.

It has the following features:
- arithmetic expressions
- block comments
- extended precision numbers via Python's decimal module
- anonymous functions
- dynamic and lexical scoping configurable by the user
- automatic tail-call optimization
- AST-optimizations: 'constant folding'
- byte-code optimizations: redundant stack push/pop elimination
- byte-code interpreter with call stack isolated from Python call stack, therefore no Python recursion limit
- closures
- eval and repl
- easily extensible:
    - can add new hard-coded node types easily
    - can add new byte-code instructions easily
    - capable of extension to compilation to assembly

# How to Use
Run `python test-nodes.py` from the current directory to run tests.

You can run a specific test with `python test-nodes.py TEST`.

Tests include:
- cons (cons/car/cdr test)
- arithmetic (arithmetic test)
- controlflow (if-else/while test)
- functions (function definition, call test)
- repl
- scoping (dynamic/lexical scoping test)
- bytecode, bytecode2, bytecode3 (bytecode generation, evaluation test)
- optimizer (bytecode and ast optimizer test)
- functionality (extra functionality test)

Author: Titus v. Köller
MIT-licensed
