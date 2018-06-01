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
