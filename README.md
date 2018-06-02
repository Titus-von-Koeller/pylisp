# Intro
This project was an attempt to build a parser, byte-code compiler and interpreter of a dynamic Lisp-like language, using a dynamic language, Python, for its implementation.
Early attempts made strategic use of Python's dynamic features with later attempts reimplmenting core structures separate from the implementation language.

A quick overview of the current architecture:

- `evaluator.py`: the evaluator implements the byte-code evaluator
- `frame.py`: the function call frame
- `insts.py`: the byte-code instructions
- `nodes.py`: the AST-nodes
- `optimizer.py`: the byte-code and AST optimizations
- `parser.py`: the parser and tokenizer

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

# Some brief notes about the design
## Parser
Parsing occurs in two steps, ass seen in the `parse()` function:
- tokenize
- build the AST

The tokenizing is accomplished via simple use of regular expressions. Our grammar is a context-free grammar and can roughly be written with the following production rules:

```
start -> sexpr start
start -> end
sexpr -> '(' termlist ')'
termlist -> term termlist
termlist -> end
term -> /\w+/ | /\d+/ | /".+"/
```

This grammar does not support infix notation. It only supports prefix notation. This simplifies parsing by eliminating ambiguities.

It's possible for us to use regular expression with backtracking to tokenize the above. In the build-AST step, we validate the grammar (for example, balancing of parantheses), using regular program logic.

Building the AST occurs in two steps: 

- In step 1, we build the token stream into a tree. This tree is represented as a Python list of lists. It is at this step, that we can check that our context-free grammar is satisfied by for example counting parantheses. 
- In step 2, we convert the list of lists into a tree of custom Python objects. These custom objects that represent the nodes of the AST subclass from `class Node`. `class Node` implements logic to dispatch to the correct type of node, given a tree expression. For example, if the first element of the tree is a `+`-sign, then this node must be an `Add`-node or a `Pos`-node. If it has only one other entry, it is a unary `Pos` node, if it has two then it is a binary `Add`-node.
	The nodes themselves understand how to parse the rest of the tree expression. 
	For example, a `Lambda`-node knows that its first term is a `Params`-list and it's second term is a `Suite`. 
	At this stage, the nodes could add additional error-checking to look for invalid forms such as unary or binary operators receiving to many arguments.

## `nodes.py`
`nodes.py` contains the definition of every AST node. Each AST node knows how to parse itself from a tree expression. In the original attempt, each AST node also implemented `__call__(self, env)`, to allow for evaluation.
	At the topmost node in a program would be a `Suite`-node, whose call would evaluate each of its children in sequence. 

Each child node would evaluate its own children as appropriate and this would allow us to execute a program, reusing the Python function stack.
	Every node would correspond to one Python function call. 
	An env variable would be threaded through these function calls to represent the environment, global and local variables that the program would operate on.

This Lisp-like language included a looping primitive as a built-in node: the `While`-node.
	Many Lisp and Scheme dialects have no looping primitives and instead rely on recursion for implementing loops.
	There is a well-know correspondence between looping and tail-recursion.

Because the initial execution approach used the Python function stack and Python has a built-in recursion limit,
	programs that rely on tail-recursion would ultimately fail.
	As a consequence, another approach was sought to allow for automatic tail-call optimization 
	and the implementation of tail recursion within fixed memory constraints.

This required building a separate function call mechanism that did not completely rely on the Python function call stack, because Python's recursion limit cannot be avoided.
	Therefore, each node implements an `__iter__(self)`, which yields bytecode instructions for this alternate execution mechanism.
	The idea is that you could use `__call__()` to evaluate the AST directly using Python's function stack or use `__iter__()` to get the bytecodes equivalent to the AST and feed them to a seperate executor/evaluator.
	Given a program, `suite`, the program can be 'compiled to bytecode' by simply calling `list(suite)`.

## `insts.py`
`insts.py` contrains the byte-code instructions. The are generated by the `__iter__()` function on the AST nodes. Our bytecode instruction set contains the following instructions:

- `Noop(Inst)`: a noop instruction
- `Missing(Inst)`: the default instruction to generate, help signal AST nodes with missing bytecode compilation
- `CallPyFunc(Inst)`: call a Python function with arguments from the stack, pushing the results to the stack
- `Halt(Inst)`: halt the running program
- `PushImm(Inst)`: push an immediate/concrete value to the stack, e.g. a number or a fixed string
- `PushVar(Inst)`: push a variable from the environment to the stack
- `PushGlobalVar(PushVar)`: push a variable from the environment's global scope to the stack
- `PushClosureVar(PushVar)`: push a variable from the environment's closure scope to the stack
- `PopVar(Inst)`: pops the variable at the top of the stack and stores it in the environment
- `PopGlobalVar(PopVar)`: pops the variable at the top of the stack and stores it in the global environment
- `PopClosureVar(PopVar)`: pops the variable at the top of the stack and stores it in the closure environment
- `StoreVar(Inst)`: stores a variable into the environment without changing the stack; used as part of an optimization, to eliminate redundant load/stores
- `Label(Inst)`: a noop instruction, that is used placeholder for a jump target label
- `JumpAlways(Inst)`: a jump instruction, that always goes to the specified label
- `JumpIfTrue(Inst)`: a jump instruction, that pops a value and goes to the specified label if that value is true
- `JumpIfFalse(Inst)`: a jump instruction, that pops a value and goes to the specified label if that value is false
- `CreateFunc(Inst)`: creates a function dynamically, popping the signature and bytecode from the stack
- `PushFunc(Inst)`: calls a native function, i.e. one created by `CreateFunc`, specified by the function's name
- `PushTailFunc(PushFunc)`: calls a native function that is tail-recursive, i.e. does not create a new stack frame
- `PushRawFunc(Inst)`: calls a native function, specified by the raw instructions
- `PopFunc(Inst)`: returns from a native function
- `ReadInput(Inst)`: read a line from the stdin
- `Evaluate(Inst)`: pops an AST from the stack and evaluates it, using the bytecode evaluator

## `evaluator.py` and `frame.py`
`frame.py` contains the definition for the `Frame` class, which represents our native function call stack frame.
A frame consists of a linear sequence of instructions, i.e. a Python list of insts objects, a program counter (PC) that identifies the next instruction to execute, a stack (implemented as a Python list) of values that instructions operate on (our evaluator is a stack-based machine), an env, which is a mapping (Python dictionary) of local, closure, and global variables to their values. 
	Having both a stack and an env mimics the operation of other real-world bytecode interpreters, such as Python's. 

If one were to implement compilation to assembly, the stack would be retained and would likely use the assembly level stack, i.e. the one which the ASM-level pop/push instructions operate on, but the env would likely have to be eliminated.
	In retaining the stack, we would likely add another index variable, in addition to the PC, so that we could use one contiguous of linear memory.
	This variable would be called the stack pointer (SP).

In our current implementation we have multiple non-contiguous stacks, one per frame, therefore no need for an SP.
	To remove the env, we would implement a symbol table approach and turn variable lookups into direct memory accesses.
	These memory accesses would use relative addressing, relative to the SP.
	This would work for all of our local variables and absolute memory addressing would work for all of the global variables. 
	However, a smarter approach might need to be taken for variables in nested closures.

`evaluator.py` implements the byte-code evaluator. The byte-code evaluator asks for the next instruction from the current frame, then executes it. It continues executing until the frame has no more instructions, in which case it pops the frame or until no more frames are left, in which case it terminates.
	The instructions are passed all of the frames, so that they may add or remove frames in the case of `PushFunc`/`PopFunc`/`Halt` or change the frame state such as jumping, pushing, popping, or storing variables.

## `optimizer.py`
 `optimizer.py` implements both a bytecode and an AST optimizer. The AST optimizer searches for set patterns in the AST and replaces those nodes with optimized variants. 
 
 Two sample AST optimizations have been implmented:
- constant folding: arythmetic expressions that only involve constant values are evaluated directly and replaced with the result. This evaluation uses the non-bytecode evaluator which we know to be safe because there will be no recursion in these evaluations. We repeatedly apply constant folding until no further optimizations can be made
- tail-recursion/TCO: We look for function calls within functions wherein the function call is the only value being returned and the function call matches the name of the function containing it.
		We replace the `Call` node with the `TailCall` node, where the `Call` node compiles to a `PushFunc` and the `TailCall` node compiles to a `PushTailFunc`. 
		The `PushTailFunc` reuses the current frame rather than creating a new frame and just resets the PC and updates the env. 
		The bytecode optimizer is a peephole optimizer, meaning it looks at windows of a set size of instructions and simplifies those instructions.
		One sample bytecode optimization has been implemented, redundant stack optimizations.
		We look for windows of size 2, containing consecutive push/pop instructions, operating on the same variable.
		We simplify these to eliminate the redundant stack operations.
		
Additional bytecode or AST optimizations should be easy to implement give this structure.

Author: Titus v. Köller
MIT-licensed
