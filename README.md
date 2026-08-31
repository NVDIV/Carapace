# Carapace DSL — Complete Language, Architecture, Semantics and Implementation Guide

**Version:** 1.0.0
**Implementation language:** Python 3.10+
**Execution backend:** Python `turtle`
**Project type:** interpreted domain-specific language (DSL) for turtle graphics

---

## How to use this document

This file is the canonical technical description of Carapace 1.0.0. It is written so that a reader who has never seen the repository can understand:

- what the language is and which problem it solves;
- what source programs look like;
- how source text becomes graphics;
- how lexical, syntactic, semantic and runtime responsibilities are separated;
- how variables, functions, scopes, recursion and `RETURN` behave;
- which errors are detected at which stage and why;
- which implementation decisions are deliberate simplifications rather than missing work;
- how the test suite validates the language contract;
- which parts are strong material for a bachelor thesis and oral defense.

The document describes the **implemented language**, not a hypothetical future version. Where a possible extension is mentioned, it is explicitly marked as a non-goal or future direction.

## Contents

1. **Language overview** — purpose, goals and deliberate non-goals.
2. **Surface language** — source files, lexical rules, commands, variables, expressions, control flow and functions.
3. **Formal grammar** — implemented grammar and recursive-descent strategy.
4. **Internal representation** — AST structure and source metadata.
5. **Front-end architecture** — lexer, parser and semantic-analysis boundaries.
6. **Semantic analysis** — symbols, passes, types, function checks and uncertain control flow.
7. **Scope and environment model** — globals, locals, shadowing and lexical lookup.
8. **Runtime execution** — interpreter, function calls, `RETURN`, recursion and validation.
9. **Turtle backend boundary** — adapter responsibilities and backend error translation.
10. **Error architecture** — phase-specific errors and diagnostics.
11. **Module-by-module architecture** — responsibilities of every project file.
12. **End-to-end walkthroughs** — source → tokens → AST → semantics → runtime.
13. **Demonstration programs** — basic examples and advanced visual examples.
14. **Testing strategy** — unit, semantic, runtime and integration verification.
15. **Packaging and project hygiene** — reproducibility and formatting conventions.
16. **Architectural decisions and trade-offs** — why the implementation is designed this way.
17. **Known limits and future extensions** — explicit boundaries of version 1.0.0.
18. **Thesis-oriented interpretation** — chapter mapping and defense arguments.
19. **Glossary** — terminology used throughout the language implementation.
20. **Final architectural invariants** — compact authoritative contract of Carapace 1.0.0.

---

# Part I. Language Overview

## 1. What Carapace is

Carapace is a small interpreted DSL designed for programmable turtle graphics. A Carapace program consists of declarative and imperative statements such as variable assignments, turtle movement commands, loops, conditions, function declarations and function calls.

A minimal program is:

```cara
REPEAT 4 [
    FORWARD 100
    RIGHT 90
]
```

This program draws a square. More complex programs can define reusable drawing procedures, compute values, perform recursive calls, return values from functions and combine local and global state.

Carapace is intentionally small enough that every major stage of a language implementation is visible in the project:

```text
source file (.cara)
        ↓
      Lexer
        ↓
      Tokens
        ↓
      Parser
        ↓
       AST
        ↓
Semantic Analyzer
        ↓
Validated AST + semantic metadata
        ↓
   Interpreter
        ↓
 Runtime environments
        ↓
 commands.py adapter
        ↓
 Python turtle / Tk
```

This separation is one of the main architectural ideas of the project. The parser does not execute programs, the semantic analyzer does not draw graphics, and the turtle adapter does not decide language semantics.

## 2. Why a DSL instead of direct Python turtle calls

Python already exposes turtle graphics, but Carapace has a different purpose. It demonstrates how a dedicated language can provide a smaller vocabulary and a domain-oriented syntax while hiding host-language details.

For example, the Python operation:

```python
turtle.forward(100)
```

becomes:

```cara
FORWARD 100
```

A reusable shape can be expressed directly in domain terms:

```cara
FUNC square size [
    REPEAT 4 [
        FORWARD size
        RIGHT 90
    ]
]

CALL square 80
```

The value of Carapace is therefore not that turtle graphics are impossible in Python. The value is that the project defines and implements a complete language contract: syntax, grammar, semantic rules, runtime behavior, diagnostics and an execution model.

## 3. Design goals

Carapace 1.0.0 follows several design goals:

1. **Readable domain syntax.** Drawing operations should be recognizable without knowledge of Python.
2. **Small but non-trivial language semantics.** The language includes variables, expressions, functions, local scopes, recursion, conditions, loops and returned values.
3. **Clear compiler/interpreter pipeline.** Lexing, parsing, semantic analysis and execution are independent stages.
4. **Predictable scope rules.** Global state and function-local state are intentionally simple and explicitly modeled.
5. **Useful diagnostics.** User-facing errors are classified by language phase and include source line information where available.
6. **Defensible simplifications.** The implementation avoids advanced features that would increase complexity without improving the central educational goal.
7. **Testable behavior.** The language contract is captured by automated tests rather than only by examples.

## 4. Deliberate non-goals

Carapace is not intended to be a general-purpose programming language. Version 1.0.0 deliberately does **not** implement:

- floating-point literals in source code;
- unary operators such as unary minus;
- booleans as first-class values;
- `ELSE`;
- comments in `.cara` source files;
- string escape sequences;
- arrays, objects or user-defined data structures;
- closures or nested functions;
- block-local scopes;
- a `global` keyword or implicit global mutation from functions;
- compile-time function return-type inference;
- full path-sensitive definite-assignment analysis;
- proof that every possible function path returns a value;
- column-level source locations;
- optimization or bytecode generation.

These are scope choices. The implemented subset is sufficient to demonstrate the full front-end/runtime architecture of an interpreted DSL.

---

# Part II. Surface Language

## 5. Source files and execution

Carapace source files use the `.cara` extension and UTF-8 encoding.

From the repository root, a program can be executed with:

```bash
python main.py examples/square.cara
```

After package installation, the console entry point is:

```bash
carapace examples/square.cara
```

The CLI also exposes inspection modes:

```bash
python main.py examples/square.cara --tokens
python main.py examples/square.cara --ast
python main.py --version
```

`--tokens` stops after lexical analysis. `--ast` stops after parsing. Normal execution continues through semantic analysis and interpretation.

The graphical backend uses Python `turtle`, which in turn depends on a working Tk environment supplied by the Python/platform installation.

## 6. Lexical elements

### 6.1 Keywords

The language recognizes these keywords:

```text
FUNC
CALL
RETURN
IF
SET
REPEAT
FORWARD
BACKWARD
LEFT
RIGHT
PENUP
PENDOWN
COLOR
WIDTH
SPEED
```

Keyword recognition is **case-insensitive**. Therefore `forward`, `Forward` and `FORWARD` all produce the `FORWARD` token.

Identifiers preserve their original spelling and case.

An important consequence is that a keyword cannot be used as an identifier. For example, `color` is still recognized as the `COLOR` keyword rather than as a parameter name.

### 6.2 Identifiers

The current lexical rule is:

```text
[A-Za-z_]+
```

Examples of valid identifiers:

```text
x
size
my_variable
_private
___
```

Digits are not part of identifiers in version 1.0.0. Thus `value2` is not one identifier under the current lexer.

### 6.3 Numbers

Source numeric literals are non-negative integers matching:

```text
\d+
```

Examples:

```cara
10
0
243
```

There is no literal syntax for `-10` or `2.5`. This does **not** mean runtime values can never be fractional: division can produce a Python numeric value such as `10 / 3` during execution.

### 6.4 Strings

String literals are enclosed in double quotes:

```cara
"red"
"forestgreen"
""
```

The lexer accepts characters until the next double quote. Escape sequences are not implemented, so embedded quoted strings are outside the current language.

### 6.5 Operators and delimiters

Arithmetic operators:

```text
+  -  *  /
```

Comparison operators:

```text
==  <  >
```

Grouping and blocks:

```text
( )
[ ]
```

Square brackets delimit statement blocks. Parentheses group expressions.

### 6.6 Whitespace and newlines

Spaces and tabs are ignored between tokens. Both Unix `LF` and Windows `CRLF` line endings are accepted.

Newlines do not act as mandatory statement terminators. Statements are separated structurally by the grammar and token sequence. Line numbers are nevertheless counted and propagated for diagnostics.

## 7. Drawing commands

### Movement

```cara
FORWARD 100
BACKWARD 50
LEFT 90
RIGHT 45
```

Arguments are expressions, not only literals:

```cara
SET size 40
FORWARD size * 2 + 10
```

### Pen state

```cara
PENUP
PENDOWN
```

### Color

```cara
COLOR "red"
```

`COLOR` requires a string. The actual color name is ultimately interpreted by the turtle backend.

### Width

```cara
WIDTH 3
```

`WIDTH` requires a positive numeric runtime value.

### Speed

```cara
SPEED 5
```

`SPEED` requires an integer from `0` through `10`, matching the turtle backend's supported speed scale.

## 8. Variables and assignment

Variables are introduced or updated with `SET`:

```cara
SET size 100
SET angle 90
SET result size * 2 + 10
```

There is no separate declaration statement. `SET` both introduces a name in the current scope and assigns its value.

The assignment target is an identifier; the assigned value is a full expression.

## 9. Arithmetic expressions

Carapace implements four binary arithmetic operations:

```cara
SET a 10 + 5
SET b 10 - 5
SET c 10 * 5
SET d 10 / 5
```

Precedence follows conventional arithmetic rules:

1. parenthesized expression;
2. multiplication and division;
3. addition and subtraction.

Thus:

```cara
SET x 10 + 20 * 3
```

is equivalent to:

```text
10 + (20 * 3)
```

Parentheses can override precedence:

```cara
SET x (10 + 20) * 3
```

Operators are left-associative because the recursive-descent parser repeatedly folds each precedence level from left to right.

All arithmetic is numeric. Carapace does not define string concatenation or string repetition via arithmetic operators.

## 10. Conditions

The `IF` form is:

```cara
IF left_expression operator right_expression [
    statements
]
```

Example:

```cara
SET distance 100

IF distance > 50 [
    COLOR "blue"
    FORWARD distance
]
```

There is no `ELSE` in version 1.0.0.

Comparison semantics are:

- `==` accepts two compatible scalar values: number/number or string/string;
- `<` and `>` require numeric operands.

If an operand has static type `UNKNOWN`, final validation is deferred until execution.

## 11. Repetition

The `REPEAT` form is:

```cara
REPEAT expression [
    statements
]
```

Example:

```cara
REPEAT 4 [
    FORWARD 100
    RIGHT 90
]
```

Semantic analysis requires a numeric expression when the type is statically known. Runtime validation additionally requires the final value to be a **non-negative integer**.

The interpreter does not silently truncate values. A fractional runtime value is not accepted as a repeat count.

## 12. Functions

### 12.1 Declaration

A function is declared with:

```cara
FUNC name parameter1 parameter2 [
    statements
]
```

Example:

```cara
FUNC rectangle width height [
    REPEAT 2 [
        FORWARD width
        RIGHT 90
        FORWARD height
        RIGHT 90
    ]
]
```

All functions are global declarations. Nested function declarations are syntactically representable by the parser's generic block structure but are rejected by semantic analysis.

### 12.2 Statement call

A function can be called for its effects:

```cara
CALL rectangle 100 50
```

A statement call does not require the function to return a value.

### 12.3 Expression call

A function call can also appear where an expression is expected:

```cara
FUNC double value [
    RETURN value * 2
]

SET size CALL double 50
FORWARD size
```

In expression context, the function must be capable of returning a value and the concrete execution path must actually execute a `RETURN`.

### 12.4 Call argument parsing

Arguments are parsed greedily as complete expressions.

```cara
CALL move 10 + 5 90
```

is interpreted as two arguments:

```text
(10 + 5)
90
```

A nested call used as an argument should be made explicit with parentheses:

```cara
CALL outer (CALL inner 10)
```

This rule keeps the existing whitespace-oriented call syntax without introducing commas or mandatory `name(...)` call syntax.

## 13. `RETURN`

`RETURN` always carries an expression:

```cara
RETURN 42
RETURN size * 2
RETURN CALL calculate size
```

`RETURN` is valid only inside a function. A top-level `RETURN` is a semantic error.

Carapace has no explicit `None` value. Instead, it distinguishes two call contexts:

- a procedure-like function may finish naturally when called as a statement;
- a call used as an expression must produce a value.

This distinction is important because “function ended without `RETURN`” is not automatically an error. It becomes an error only if the caller requires a value.

## 14. Recursion

Direct and mutual recursion are supported.

A recursive example:

```cara
FUNC countdown n [
    IF n > 0 [
        CALL countdown n - 1
    ]
]

CALL countdown 5
```

Recursion works because all global function declarations are collected before function bodies and ordinary execution are processed. Each call also receives a fresh local runtime environment, so recursive invocations do not overwrite each other's parameter values.

---

# Part III. Formal Grammar

## 15. Implemented grammar

The repository contains `src/grammar.txt`. The implemented grammar can be summarized as:

```text
<Program>      ::= <Statement>* EOF

<Statement>    ::= <Command>
                 | <Loop>
                 | <Assignment>
                 | <IfStatement>
                 | <FunctionDef>
                 | <FunctionCall>
                 | <ReturnStatement>

<FunctionDef>  ::= "FUNC" <Identifier> <Identifier>* "[" <Statement>* "]"

<FunctionCall> ::= "CALL" <Identifier> <Expression>*

<ReturnStatement> ::= "RETURN" <Expression>

<IfStatement>  ::= "IF" <Expression> <ComparisonOp> <Expression>
                   "[" <Statement>* "]"

<ComparisonOp> ::= "==" | "<" | ">"

<Assignment>   ::= "SET" <Identifier> <Expression>

<Command>      ::= "FORWARD" <Expression>
                 | "BACKWARD" <Expression>
                 | "LEFT" <Expression>
                 | "RIGHT" <Expression>
                 | "PENUP"
                 | "PENDOWN"
                 | "COLOR" <Expression>
                 | "WIDTH" <Expression>
                 | "SPEED" <Expression>

<Loop>         ::= "REPEAT" <Expression> "[" <Statement>* "]"

<Expression>   ::= <Term> (("+" | "-") <Term>)*

<Term>         ::= <Factor> (("*" | "/") <Factor>)*

<Factor>       ::= <Number>
                 | <String>
                 | <Identifier>
                 | "(" <Expression> ")"
                 | <FunctionCall>
```

## 16. Why recursive descent is suitable here

Carapace uses a hand-written recursive-descent parser. This is appropriate because:

- the grammar is compact;
- expression precedence has only a few levels;
- control-flow constructs are explicit and bracket-delimited;
- the implementation remains easy to connect to the formal grammar in a thesis;
- parser errors can be generated at the exact point where an expected token is missing.

The core precedence decomposition is conventional:

```text
parse_expression → parse_term → parse_factor
```

`parse_expression()` handles `+` and `-`, `parse_term()` handles `*` and `/`, and `parse_factor()` handles literals, identifiers, parentheses and function calls.

---

# Part IV. Internal Representation

## 17. The Abstract Syntax Tree

The parser does not execute tokens directly. It converts them into typed AST nodes defined in `src/ast.py`.

This is a major architectural boundary:

```text
Tokens describe lexical categories.
AST nodes describe program structure.
```

For example:

```cara
SET size 10 + 20
```

conceptually becomes:

```text
SetNode
├── name: "size"
└── value: BinOpNode
    ├── left: LiteralNode(10)
    ├── op: PLUS
    └── right: LiteralNode(20)
```

## 18. AST node catalogue

### Base and expression nodes

- `ASTNode` — common base carrying source-line metadata;
- `LiteralNode` — numeric or string literal;
- `VariableNode` — variable reference;
- `BinOpNode` — binary arithmetic expression.

### Assignment and commands

- `SetNode`;
- `ForwardNode`;
- `BackwardNode`;
- `LeftNode`;
- `RightNode`;
- `PenUpNode`;
- `PenDownNode`;
- `ColorNode`;
- `WidthNode`;
- `SpeedNode`.

### Control flow

- `RepeatNode` — iteration expression and statement body;
- `IfNode` — left operand, comparison operator, right operand and body.

### Functions

- `FunctionDefNode` — name, parameter names and body;
- `FunctionCallNode` — function name and argument expressions;
- `ReturnNode` — returned expression.

## 19. Source metadata and AST equality

Every AST node can carry a source `line`.

The field is declared with `compare=False`. This is deliberate: source location is metadata, not part of the structural meaning of the tree. Two ASTs with the same language structure but originating on different lines should remain structurally comparable in tests.

The current implementation tracks lines but not columns. Line-only diagnostics are a conscious complexity trade-off for this version.

---

# Part V. Front-End Architecture

## 20. Lexer responsibilities

`src/lexer.py` is responsible for:

- scanning source text;
- recognizing keywords, identifiers, literals, delimiters and operators;
- converting numeric source text to integer values;
- removing quote delimiters from string token values;
- counting source lines;
- rejecting unsupported characters;
- appending an explicit `EOF` token.

It is **not** responsible for:

- validating grammar;
- deciding whether a function exists;
- deciding whether `FORWARD "red"` is meaningful;
- executing graphics.

These boundaries matter because an invalid program should fail at the earliest stage that has enough information to classify the problem correctly.

## 21. Parser responsibilities

`src/parser.py` is responsible for:

- consuming the token sequence;
- validating syntactic structure;
- enforcing required delimiters and token forms;
- implementing arithmetic precedence;
- building AST nodes;
- attaching source lines to nodes;
- detecting unclosed `REPEAT`, `IF` and `FUNC` blocks.

It intentionally does **not** reject semantically invalid but syntactically valid programs such as:

```cara
RETURN 10
```

or:

```cara
CALL missing_function
```

Those forms have valid syntax. Their invalidity depends on semantic context.

## 22. Why semantic analysis is a separate stage

Without a semantic analyzer, the parser would gradually accumulate responsibilities such as function lookup, scope validation and type checking. That would mix two different questions:

1. **Can this token sequence form a valid sentence in the grammar?**
2. **Does that valid sentence make sense in this program?**

Carapace answers the first question in the parser and the second in `semantic_analyzer.py`.

This separation also prevents the interpreter from becoming the first place where every mistake is discovered. Errors such as duplicate function declarations or wrong function arity can be reported before any graphics are initialized.

---

# Part VI. Semantic Analysis

## 23. Semantic model

The semantic analyzer validates program meaning without executing user code. It maintains symbolic scopes that are separate from runtime environments.

This distinction is fundamental:

```text
Semantic scope → what names and type facts are known before execution.
Runtime environment → what concrete values exist during one execution.
```

A semantic symbol is metadata. A runtime variable is an actual value.

## 24. Lightweight static type knowledge

Carapace uses three semantic type states:

```text
NUMBER
STRING
UNKNOWN
```

`UNKNOWN` does not mean “invalid.” It means that the analyzer does not have enough static information and must allow runtime validation to decide.

Examples:

```cara
SET x 10
```

`x` is statically known as `NUMBER`.

A function parameter:

```cara
FUNC move x [
    FORWARD x
]
```

has static type `UNKNOWN`, because Carapace has no parameter type annotations.

This allows the analyzer to reject errors it can prove while avoiding false claims about values that only become known during execution.

## 25. Semantic symbols

### `VariableSymbol`

Stores:

- variable name;
- currently known static type;
- source line.

### `FunctionSymbol`

Stores:

- function name;
- parameter names;
- corresponding `FunctionDefNode`;
- whether any `RETURN` exists structurally in the function body;
- source line.

### `SemanticResult`

Contains the validated global semantic scope and exposes the function registry used by the interpreter.

## 26. Multi-pass semantic analysis

Carapace does not analyze the AST in only one naïve pass. Its order is designed around function visibility and global information.

### Pass 1 — collect global functions

All direct top-level `FUNC` declarations are registered before calls are analyzed.

Consequences:

- a function can be called before its textual declaration;
- function A can call a later function B;
- direct recursion is possible;
- mutual recursion is possible.

Duplicate function names and duplicate parameter names are rejected during declaration processing.

### Pass 2 — analyze top-level ordinary statements

Non-function statements are analyzed in source order.

This supports useful detection of obvious top-level use-before-`SET`:

```cara
FORWARD x
SET x 10
```

At the first statement, `x` is not yet a known top-level variable and a semantic error is produced.

### Pass 3 — analyze function bodies

Function bodies are analyzed after top-level variable symbols have been collected.

Each function receives a fresh semantic function scope containing its parameters and a parent link to the global semantic scope.

This means a function can semantically refer to a global variable symbol declared at top level even if the textual `SET` occurs later in the file. Whether the value has actually been initialized at the moment of a concrete call remains a runtime question.

## 27. Semantic scopes

There are two semantic scope kinds:

```text
SemanticGlobalScope
SemanticFunctionScope → parent: SemanticGlobalScope
```

There are no `IF` scopes, no `REPEAT` scopes and no nested function scopes.

This matches the runtime scope model intentionally.

## 28. Variables inside uncertain control flow

`IF` can execute zero times and `REPEAT` can execute zero times. Therefore assignments inside these constructs must not be treated as guaranteed runtime initialization.

Carapace uses a deliberately lightweight, path-insensitive strategy:

- blocks do not introduce a new scope;
- names assigned inside a block belong to the enclosing semantic scope;
- if an already-known variable's type is changed inside an uncertain block, its post-block type becomes `UNKNOWN` because the assignment may or may not execute;
- runtime lookup still determines whether a concrete value actually exists on the executed path.

Example:

```cara
SET x 10

IF condition > 0 [
    SET x "red"
]
```

After the `IF`, the analyzer cannot safely state that `x` is definitely `NUMBER` or definitely `STRING`, so its known type becomes `UNKNOWN`.

This avoids unsound type assumptions without implementing a full control-flow graph and data-flow lattice.

## 29. Arithmetic semantic rules

Arithmetic operators require numeric values when operand types are statically known.

Valid:

```cara
SET x 10 + 20
```

Rejected semantically:

```cara
SET x "a" + "b"
```

Deferred to runtime when necessary:

```cara
FUNC add_ten value [
    RETURN value + 10
]
```

The parameter type is `UNKNOWN`, so the function definition itself is valid. `CALL add_ten "hello"` later fails at runtime when the concrete string is used in arithmetic.

## 30. Command semantic rules

Known type requirements:

| Construct | Required type |
| --- | --- |
| `FORWARD` | `NUMBER` |
| `BACKWARD` | `NUMBER` |
| `LEFT` | `NUMBER` |
| `RIGHT` | `NUMBER` |
| `WIDTH` | `NUMBER` |
| `SPEED` | `NUMBER` |
| `REPEAT` | `NUMBER` |
| `COLOR` | `STRING` |
| `PENUP` | no argument |
| `PENDOWN` | no argument |

Runtime-only constraints such as positive width or integer repeat count are intentionally not presented as static type rules.

## 31. Function semantic rules

The analyzer checks:

- referenced function exists;
- number of arguments equals number of parameters;
- nested function declarations are forbidden;
- duplicate functions are forbidden;
- duplicate parameter names within one function are forbidden;
- `RETURN` appears only inside a function;
- a function with no `RETURN` anywhere cannot be used as an expression.

The analyzer deliberately does **not** prove that every execution path reaches a `RETURN`.

Consider:

```cara
FUNC maybe value [
    IF value > 0 [
        RETURN value
    ]
]
```

The function contains a `RETURN`, so expression usage is potentially valid. Whether a concrete call returns depends on the runtime value.

```cara
SET a CALL maybe 10
```

returns `10`.

```cara
SET b CALL maybe 0
```

falls through and produces a runtime error because expression context requires a value.

This two-stage policy is much simpler than full return-path analysis while remaining semantically precise at execution time.

---

# Part VII. Scope and Environment Model

## 32. Runtime environments

Runtime state is implemented in `src/environment.py` with two explicit classes:

```text
GlobalEnvironment
FunctionEnvironment
```

### `GlobalEnvironment`

Stores:

```text
variables: global concrete values
functions: all global function definitions
```

### `FunctionEnvironment`

Stores:

```text
variables: parameters and local values for one active call
parent: the one GlobalEnvironment
```

A new `FunctionEnvironment` is created for every call.

## 33. The central lexical-scope invariant

Every function environment points **directly to the global environment**:

```text
FunctionEnvironment.parent → GlobalEnvironment
```

It never points to the caller's function environment.

This prevents accidental dynamic scoping.

Consider:

```cara
SET x 10

FUNC B [
    FORWARD x
]

FUNC A [
    SET x 100
    CALL B
]

CALL A
```

Correct behavior: `B` sees global `x = 10`.

Incorrect dynamic-scope behavior would let `B` see `A`'s local `x = 100`. Carapace explicitly avoids this by separating the call stack from the lexical environment parent chain.

## 34. Call stack versus scope chain

These concepts are related but not identical.

The **call stack** answers:

> Which function invocation should execution return to after this call?

The **scope chain** answers:

> Where should a variable name be looked up?

During nested calls, the interpreter saves and restores the previous active environment to model call execution. But the newly created callee environment's lexical parent is still global, not the previous environment.

This is one of the most important architectural decisions in the language.

## 35. Variable lookup

At top level:

```text
lookup(name) → global variables
```

Inside a function:

```text
lookup(name)
    1. current function locals/parameters
    2. global variables
```

No caller-local lookup exists.

## 36. Assignment and shadowing

`SET` always writes to the **current** runtime environment.

At top level:

```cara
SET x 10
```

writes globally.

Inside a function:

```cara
FUNC test [
    SET x 20
]
```

writes locally, even if a global `x` already exists.

Therefore local-over-global shadowing is allowed:

```cara
SET x 10

FUNC test [
    SET x 20
    FORWARD x
]

CALL test
FORWARD x
```

The first movement uses `20`; the final top-level movement uses global `10`.

There is no implicit mutation of an existing global variable from inside a function. A future language could add an explicit `global` declaration, but Carapace 1.0.0 deliberately keeps assignment local and predictable.

## 37. Parameters

Function parameters are initialized as local variables in the new function environment.

They may shadow globals:

```cara
SET size 100

FUNC draw size [
    FORWARD size
]

CALL draw 20
```

Inside `draw`, `size` is `20`; the global `size` remains `100`.

Arguments are evaluated **in the caller environment before switching to the callee environment**. This allows a caller local to be passed explicitly even though it is not directly visible to the callee.

## 38. `IF` and `REPEAT` do not create scopes

Blocks reuse the current environment.

At top level, a `SET` executed inside `IF` or `REPEAT` writes globally. Inside a function, it writes to that function's local environment.

This decision keeps the language scope model simple:

```text
program scope
function-call scope
```

rather than introducing additional nested lexical environments for every block.

---

# Part VIII. Runtime Execution

## 39. Interpreter initialization

The interpreter receives:

```text
AST
SemanticResult
```

It creates a fresh `GlobalEnvironment` and preloads every validated global function into that environment before ordinary statements execute.

Therefore textual function declaration order does not control runtime visibility.

## 40. Program execution algorithm

Conceptually:

```text
1. initialize turtle graphics
2. for each top-level AST node in source order:
   a. skip FunctionDefNode (already registered)
   b. execute every other statement
3. finalize turtle graphics
```

If execution raises an error, graphics finalization is attempted, but a cleanup failure is not allowed to replace the original program/runtime failure.

## 41. Expression evaluation

The interpreter's `evaluate()` handles:

- literals;
- variable lookup;
- arithmetic binary operations;
- function calls used as expressions.

It does not execute arbitrary statement nodes as values.

## 42. Runtime arithmetic validation

Even after semantic analysis, runtime validation remains necessary because some static types are `UNKNOWN`.

The interpreter checks concrete values before arithmetic. `bool` is explicitly excluded from Carapace numeric values even though Python's `bool` is technically a subclass of `int`.

Division by zero raises a Carapace runtime error rather than leaking Python `ZeroDivisionError` to the language user.

## 43. Runtime command constraints

Some rules depend on actual values rather than only static types.

### `REPEAT`

Must resolve to a non-negative integer.

### `WIDTH`

Must resolve to a positive number.

### `SPEED`

Must resolve to an integer in `[0, 10]`.

### `COLOR`

Must resolve to a string. The turtle backend then decides whether the supplied string is a valid color name.

## 44. Function-call runtime algorithm

A call follows this sequence:

```text
1. resolve function in GlobalEnvironment
2. evaluate every argument in the caller environment
3. defensively validate arity
4. create fresh FunctionEnvironment(parent=global)
5. bind parameters to evaluated argument values
6. save caller's active environment
7. switch interpreter.env to the new function environment
8. execute function body
9. catch ReturnSignal if RETURN executes
10. restore the previous environment in finally
11. if expression context required a value and no RETURN occurred:
       raise RuntimeError
12. otherwise return the produced value or complete the statement call
```

The `finally` restoration is essential. It guarantees correct interpreter state after:

- normal function completion;
- `RETURN`;
- nested function calls;
- runtime errors.

## 45. Runtime implementation of `RETURN`

`RETURN` is not modeled as an ordinary language error. The interpreter raises an internal `ReturnSignal` carrying the returned value.

`ReturnSignal` propagates naturally through nested execution such as `IF` and `REPEAT`, and is caught only at the active function-call boundary.

This is a common interpreter technique because it avoids manually threading a “has returned” flag through every control-flow executor.

`ReturnSignal` is intentionally **not** a subclass of `CarapaceError`.

## 46. Why a private no-return sentinel is needed

The interpreter uses a private sentinel object to distinguish:

```text
function executed RETURN with some value
```

from:

```text
function body reached the end without executing RETURN
```

Using Python `None` for this distinction would incorrectly introduce a hidden language-level `None` value. The sentinel keeps host-language implementation state separate from Carapace values.

## 47. Recursion at runtime

Every recursive call creates a new `FunctionEnvironment`. Parameters and locals therefore belong to a specific invocation.

The lexical parent remains the single global environment at every recursion depth:

```text
call branch(120) ── local env #1 ──→ global
call branch(80)  ── local env #2 ──→ global
call branch(53)  ── local env #3 ──→ global
```

The environments are nested in time through the call stack, but not chained lexically through one another.

---

# Part IX. Turtle Backend Boundary

## 48. Purpose of `commands.py`

`src/commands.py` is deliberately thin. It maps validated interpreter operations to Python turtle calls:

```text
execute_forward → turtle.forward
execute_backward → turtle.backward
execute_left → turtle.left
execute_right → turtle.right
execute_penup → turtle.penup
execute_pendown → turtle.pendown
execute_color → turtle.color
execute_width → turtle.pensize
execute_speed → turtle.speed
```

It also initializes and finalizes graphics.

This module is an adapter, not a semantic layer.

## 49. Why turtle calls are isolated

Keeping turtle access behind a small adapter provides several benefits:

- interpreter logic can be tested without opening GUI windows;
- language validation remains independent of backend mechanics;
- backend calls can be mocked in unit tests;
- expected turtle/Tk value errors can be translated at one boundary;
- a future backend could be introduced with fewer changes to the language core.

## 50. Backend error translation

The interpreter translates expected user-facing backend failures such as invalid turtle color values into Carapace `RuntimeError`.

It does **not** blindly catch every exception and label it a language error. Unexpected implementation failures are allowed to remain system/internal errors.

This distinction prevents real programming bugs from being misleadingly reported as mistakes in a `.cara` program.

---

# Part X. Error Architecture

## 51. Error hierarchy

Carapace defines:

```text
CarapaceError
├── SourceFileError
├── LexerError
├── ParserError
├── SemanticError
└── RuntimeError

ReturnSignal(Exception)   # separate internal control flow
```

The phase-specific hierarchy makes an error's origin explicit.

## 52. `SourceFileError`

Used for source acquisition problems such as:

- wrong file extension;
- missing file;
- path is not a file;
- file cannot be read as expected.

## 53. `LexerError`

Used when source characters cannot be tokenized under the lexical rules.

Example category:

```text
unexpected unsupported character
```

## 54. `ParserError`

Used for syntactically invalid token sequences, including:

- missing required tokens;
- invalid expression factor;
- unexpected statement token;
- malformed comparison header;
- unclosed blocks.

## 55. `SemanticError`

Used when syntax is valid but program meaning is statically invalid, including:

- duplicate function declaration;
- duplicate function parameters;
- nested function declaration;
- undefined function;
- wrong function arity;
- top-level `RETURN`;
- statically known command type mismatch;
- statically known arithmetic type mismatch;
- invalid known comparison types;
- obvious undefined variable use.

## 56. `RuntimeError`

Used when validity depends on concrete execution, including:

- variable symbol exists semantically but no runtime value was initialized on the executed path;
- division by zero;
- `UNKNOWN` static value resolves to an invalid runtime type;
- invalid repeat count;
- invalid width or speed value;
- expression-call path reaches function end without `RETURN`;
- expected turtle/Tk user-value error.

## 57. `ReturnSignal`

`ReturnSignal` is internal control flow. It must never be caught by the CLI as a user-facing `CarapaceError` during correct interpreter behavior, because the function-call executor catches it at the appropriate boundary.

## 58. Source locations

Token line numbers are propagated into AST nodes and then used by semantic and runtime errors.

Typical diagnostics are of the form:

```text
Line 5: Function 'draw' is already defined
Line 8: Division by zero
```

Version 1.0.0 intentionally tracks line numbers only. Column tracking would require richer token position metadata and is a reasonable future extension, but it is not necessary for the current project goals.

## 59. CLI error boundary

`main.py` catches `CarapaceError` and reports it as:

```text
Carapace Error: ...
```

Unexpected exceptions are reported separately as internal system errors.

This preserves the distinction between a bad Carapace program and a defect/environmental failure in the interpreter itself.

---

# Part XI. Module-by-Module Architecture

## 60. Repository structure

The core implementation is:

```text
main.py
src/
├── __init__.py
├── lexer.py
├── ast.py
├── parser.py
├── semantic_analyzer.py
├── environment.py
├── interpreter.py
├── commands.py
├── errors.py
└── grammar.txt
```

Tests live under `tests/`, and runnable demonstration programs live under `examples/`.

## 61. `src/lexer.py`

Owns lexical recognition and token production.

Key abstractions:

```text
TokenType
Token
Lexer
KEYWORDS
```

The output contract is a list of tokens terminated by `EOF`.

## 62. `src/ast.py`

Owns the language's structural representation. It has no parsing algorithm and no runtime behavior.

Keeping AST classes outside `parser.py` is important because both semantic analysis and interpretation consume the same representation without depending conceptually on parser internals.

## 63. `src/parser.py`

Owns recursive-descent parsing and AST construction.

It depends on:

- token definitions from the lexer;
- AST node definitions;
- `ParserError`.

It does not depend on runtime environments, turtle or semantic symbols.

## 64. `src/semantic_analyzer.py`

Owns static program-meaning validation.

Key abstractions:

```text
ValueType
VariableSymbol
FunctionSymbol
SemanticGlobalScope
SemanticFunctionScope
SemanticResult
SemanticAnalyzer
```

It consumes AST but does not execute user code.

## 65. `src/environment.py`

Owns concrete runtime namespaces.

The explicit split between `GlobalEnvironment` and `FunctionEnvironment` makes scope invariants visible in code instead of encoding them implicitly in a generic dictionary chain.

## 66. `src/interpreter.py`

Owns execution semantics:

- evaluates expressions;
- executes statements;
- creates function environments;
- manages call-state restoration;
- validates runtime-dependent values;
- implements `RETURN` control flow;
- delegates graphics operations to `commands.py`.

## 67. `src/commands.py`

Owns only the turtle adapter boundary.

It intentionally remains small.

## 68. `src/errors.py`

Owns the public language error taxonomy and the private `ReturnSignal` implementation mechanism.

## 69. `main.py`

Owns CLI orchestration:

```text
read source
→ lex
→ optionally print tokens
→ parse
→ optionally print AST
→ semantic analysis
→ interpret
```

It should remain thin rather than absorb language logic.

## 70. `src/grammar.txt`

Provides a compact formal grammar reference aligned with the parser.

## 71. `pyproject.toml`

Defines package metadata:

- project name `carapace`;
- version `1.0.0`;
- Python requirement `>=3.10`;
- console entry point `carapace = main:main`;
- package inclusion of `src` and `grammar.txt`;
- pytest configuration.

---

# Part XII. End-to-End Walkthroughs

## 72. Walkthrough: arithmetic drawing command

Source:

```cara
SET size 50
FORWARD size * 2 + 10
```

### Lexing

The source becomes token categories conceptually equivalent to:

```text
SET IDENTIFIER(size) NUMBER(50)
FORWARD IDENTIFIER(size) MULTIPLY NUMBER(2) PLUS NUMBER(10)
EOF
```

### Parsing

The first line becomes `SetNode`.

The second becomes `ForwardNode` whose distance is a binary tree respecting precedence:

```text
PLUS
├── MULTIPLY
│   ├── Variable(size)
│   └── Literal(2)
└── Literal(10)
```

### Semantic analysis

`size` becomes a global `VariableSymbol` with known type `NUMBER`.

The `FORWARD` expression is inferred as `NUMBER`, so it is statically compatible with the command.

### Runtime

`SET size 50` stores `50` in `GlobalEnvironment.variables`.

The expression evaluates to:

```text
50 * 2 + 10 = 110
```

The interpreter validates `110` as numeric and delegates to `commands.execute_forward(110)`.

## 73. Walkthrough: local shadowing

Source:

```cara
SET x 10

FUNC draw [
    SET x 50
    FORWARD x
]

CALL draw
RIGHT 90
FORWARD x
```

### Static model

There is one global variable symbol `x` and a function `draw`.

Inside `draw`, local `SET x 50` introduces/shadows a function-local symbol.

### Runtime model

Before the call:

```text
GlobalEnvironment.variables = {x: 10}
```

During `draw`:

```text
FunctionEnvironment.variables = {x: 50}
FunctionEnvironment.parent = GlobalEnvironment
```

`FORWARD x` reads local `50`.

After the call, the function environment is discarded/restored away. Global `x` is still `10`, so the final `FORWARD x` uses `10`.

## 74. Walkthrough: returned value

Source:

```cara
FUNC double value [
    RETURN value * 2
]

SET distance CALL double 40
FORWARD distance
```

The function symbol is collected before execution.

When `CALL double 40` is evaluated in expression context:

1. `40` is evaluated in the caller;
2. a new function environment is created;
3. local `value = 40` is bound;
4. `RETURN value * 2` evaluates to `80`;
5. `ReturnSignal(80)` exits the function body;
6. caller environment is restored in `finally`;
7. `80` becomes the `SET` expression value;
8. global `distance = 80` is stored;
9. turtle moves forward by `80`.

## 75. Walkthrough: conditional missing return

Source:

```cara
FUNC maybe value [
    IF value > 0 [
        RETURN value
    ]
]

SET result CALL maybe 0
```

Semantic analysis accepts expression use because the function structurally contains a `RETURN`.

At runtime, `value > 0` is false. No `RETURN` executes. The function reaches its end, and because this call is used as an expression, the interpreter raises:

```text
Function 'maybe' did not return a value
```

This example demonstrates the intentional split between lightweight static return analysis and precise runtime-path behavior.

## 76. Walkthrough: recursive fractal

The provided `examples/fractal_tree.cara` defines a recursive `branch` function.

Each call:

- receives its own local `length` parameter;
- draws a branch;
- calls itself twice with `length * 2 / 3`;
- restores turtle orientation and position before returning naturally.

The recursion terminates because recursive calls occur only under:

```cara
IF length > 8 [ ... ]
```

This example demonstrates that Carapace functions are not merely textual macros. They have real parameter binding, independent invocation state, arithmetic arguments, conditional execution and recursion.

---

# Part XIII. Demonstration Programs

## 77. Existing basic examples

The `examples/` directory contains small focused programs for:

- arithmetic expressions;
- conditions;
- variables;
- functions and returned values;
- square/star drawing;
- nested repetition;
- spiral-style drawings;
- pen/color/width/speed commands.

These are useful as individual language feature demonstrations.

## 78. Rosette

`examples/rosette.cara` defines one reusable `square` function and rotates the turtle between calls:

```cara
FUNC square size [
    REPEAT 4 [
        FORWARD size
        RIGHT 90
    ]
]

REPEAT 36 [
    CALL square 120
    RIGHT 10
]
```

The visual result is a dense circular rosette. Technically it demonstrates composition of function calls and nested repetition.

## 79. Fractal tree

`examples/fractal_tree.cara` uses direct recursion, arithmetic call arguments and `IF` as a recursion guard.

It is one of the strongest demonstrations of the language's runtime architecture because every branch depends on fresh function-local state.

## 80. Koch snowflake

`examples/koch_snowflake.cara` recursively implements a Koch curve and repeats it three times to form a snowflake.

The example is particularly useful because it combines:

- recursion;
- arithmetic expressions;
- division producing runtime fractional numbers;
- multiple recursive calls;
- conditional base/recursive cases;
- function parameters;
- repeated composition into a final graphic.

It also illustrates an interesting consequence of the language design: source literals are integers, but runtime arithmetic can still produce non-integer numeric values.

---

# Part XIV. Testing Strategy

## 81. Why the tests are part of the language specification

For an interpreter, tests do more than check implementation details. They define observable language behavior.

A parser test specifying the AST for `10 + 20 * 3` records precedence semantics. A scope test showing that a callee cannot see caller locals records lexical-scope semantics. A runtime test requiring missing-return failure in expression context records function-value semantics.

The suite therefore serves as an executable specification.

## 82. Test organization

The suite is separated by responsibility:

```text
tests/
├── test_lexer.py
├── test_parser.py
├── test_parser_commands.py
├── test_parser_control_flow.py
├── test_parser_expressions.py
├── test_parser_programs.py
├── test_environment.py
├── test_semantic_declarations.py
├── test_semantic_scopes.py
├── test_semantic_functions.py
├── test_semantic_types.py
├── test_interpreter.py
├── test_interpreter_scopes.py
├── test_interpreter_functions.py
├── test_interpreter_control_flow.py
├── test_interpreter_commands.py
├── test_interpreter_errors.py
├── test_errors.py
├── test_integration.py
└── test_main.py
```

This mirrors the architecture rather than placing all behavior into one monolithic test file.

## 83. Lexer coverage themes

Lexer tests cover:

- keywords and case handling;
- identifiers;
- numbers;
- strings including empty strings;
- arithmetic and comparison operators;
- parentheses and brackets;
- spaces, tabs, newlines and CRLF;
- unsupported characters;
- source line tracking;
- EOF production.

## 84. Parser coverage themes

Parser tests cover:

- every command node;
- assignment;
- arithmetic precedence and associativity;
- parenthesized expressions;
- conditions;
- repetition;
- functions and calls;
- returned expressions;
- nested blocks;
- complete programs;
- malformed expressions and statements;
- unclosed blocks;
- AST structure rather than only node type.

## 85. Environment and scope tests

These tests isolate scope mechanics without involving the parser:

- global get/set;
- local get/set;
- local-over-global shadowing;
- local assignment does not mutate global state;
- function parent is global;
- caller local is invisible to callee.

This direct unit testing is valuable because scope bugs are otherwise difficult to diagnose through graphics output alone.

## 86. Semantic analyzer tests

Semantic tests cover:

- forward function calls;
- direct and mutual recursion declarations;
- duplicate functions and parameters;
- nested-function rejection;
- undefined variables/functions;
- top-level sequential variable rules;
- function scope visibility;
- arity;
- `RETURN` context;
- statement versus expression calls;
- known and unknown type behavior;
- command type requirements;
- arithmetic and comparison types;
- control-flow type uncertainty.

## 87. Interpreter tests

Interpreter tests use a mocked command backend and cover:

- expression evaluation;
- global and local values;
- shadowing;
- function parameter binding;
- argument evaluation in caller context;
- nested-call restoration;
- `RETURN` propagation;
- recursion;
- `IF` and `REPEAT` execution;
- command delegation;
- runtime value constraints;
- division by zero;
- path-dependent uninitialized values;
- backend error translation.

## 88. Integration tests

Integration tests exercise multiple language phases together and ensure that semantically invalid programs stop before graphics initialization.

They are intentionally fewer than focused unit tests because their job is to validate pipeline integration, not duplicate every parser edge case.

## 89. Current regression status

In the final verification run, the suite contains:

```text
442 tests
442 passed
```

A coverage run reports approximately **89% total statement coverage** across `main.py` and `src/`.

Core language modules are strongly covered:

| Module | Approx. statement coverage |
| --- | ---: |
| `src/ast.py` | 100% |
| `src/parser.py` | 100% |
| `src/lexer.py` | 99% |
| `src/environment.py` | 97% |
| `src/semantic_analyzer.py` | 96% |
| `src/interpreter.py` | 90% |
| `src/errors.py` | 100% |

Lower direct coverage in `commands.py` is expected because turtle GUI calls are deliberately mocked at the interpreter boundary. Lower `main.py` coverage reflects CLI/UI orchestration rather than weakness in the core language algorithms.

---

# Part XV. Packaging, Reproducibility and Project Hygiene

## 90. Package configuration

The project builds with setuptools from `pyproject.toml`.

The package configuration includes:

```text
src package
main module
grammar.txt package data
```

The installed console script is named `carapace`.

## 91. Versioning

The canonical project version is:

```text
1.0.0
```

It is aligned between package metadata and `src.__version__`.

## 92. Formatting and documentation conventions

The final source tree follows these presentation conventions:

- four spaces for Python indentation;
- no tab-indented Python code;
- no trailing whitespace;
- final newline in text files;
- module docstrings for core implementation modules;
- docstrings for classes and methods/functions;
- comments explain design intent rather than restating obvious syntax;
- AST, semantic and runtime modules use explicit section separators for major phases;
- `.cara` examples use four-space block indentation.

The final editorial pass changes documentation and formatting only. Executable Python AST structure is verified against the pre-formatting project to ensure that the language implementation itself was not altered by this cleanup.

## 93. Build and smoke-test expectations

A reproducibility check should include:

```bash
python -m compileall src main.py
python -m pytest
python -m build
```

After installing the resulting wheel in an isolated environment, at minimum the package imports and the Lexer → Parser → SemanticAnalyzer pipeline should work.

---

# Part XVI. Architectural Decisions and Trade-offs

## 94. Why functions are globally declared

Global-only functions avoid closures, nested declaration lifetimes and lexical capture rules. This provides enough abstraction for reusable and recursive drawing procedures while keeping the scope model teachable.

Because declarations are collected before analysis/execution, source order does not artificially restrict recursion or cross-function calls.

## 95. Why function locals cannot implicitly mutate globals

Allowing `SET x` inside a function to search outward and mutate an existing global would make assignment meaning context-sensitive in a subtle way.

Carapace instead uses:

```text
read: local → global
write: current scope only
```

This asymmetry is simple and predictable. Local shadowing is explicit through behavior, and global state is protected from accidental function-local assignment.

## 96. Why caller locals are invisible

If callees could see caller locals, variable meaning would depend on the dynamic call path rather than lexical program structure. That is dynamic scoping.

Carapace deliberately uses lexical-style function visibility: a function sees its own locals/parameters and globals, independent of who called it.

This is implemented concretely by `FunctionEnvironment(parent=global_env)`.

## 97. Why blocks do not create scopes

Block scopes would require additional environment creation for every `IF` and `REPEAT`, plus decisions about variable lifetime after a block.

For a drawing DSL, the simpler model is useful:

```text
only global scope and function-call scope
```

The semantic analyzer still accounts for uncertain execution without creating block-local namespaces.

## 98. Why static typing is intentionally lightweight

A full type system would require function signatures, return-type inference, flow-sensitive joins and potentially annotations.

Carapace instead uses `NUMBER`, `STRING` and `UNKNOWN` so it can catch obvious mistakes early while preserving a dynamically evaluated programming style.

This design also creates a clear thesis discussion about the boundary between static and dynamic validation.

## 99. Why no all-path return proof is performed

All-path return analysis would require control-flow reasoning. In a language with `IF` but no `ELSE`, loops with variable counts and recursion, even a small analysis quickly becomes more complex than the project needs.

Carapace therefore performs a structural check:

```text
Does the function contain any RETURN?
```

and a runtime check:

```text
Did this concrete expression call actually execute RETURN?
```

This division provides useful safety with limited complexity.

## 100. Why `RETURN` uses an exception-like signal internally

A return must immediately exit nested statements and loops. A private exception-like signal naturally unwinds Python control flow until the function-call executor catches it.

This is cleaner than requiring every `execute()` call to return and propagate a custom status object.

The design remains safe because `ReturnSignal` is explicitly separated from user-facing `CarapaceError`.

## 101. Why runtime environments and semantic scopes are different classes

They answer different questions.

Semantic scope contains facts such as:

```text
name exists
known type is NUMBER/STRING/UNKNOWN
function has parameters [...]
```

Runtime environment contains concrete state such as:

```text
x = 42
color_name = "red"
```

Merging the two would make analysis depend on execution and execution depend on static metadata in confusing ways. Separate abstractions preserve phase boundaries.

## 102. Why turtle is behind an adapter

The language core should be testable in headless environments. A thin adapter lets tests mock graphics and assert exact drawing commands without opening windows.

It also makes the difference between **language semantics** and **rendering backend behavior** explicit.

## 103. Why source locations are line-only

Columns would improve diagnostics, but require position tracking across lexer matches and propagation of richer source spans through AST nodes.

Line-only positions provide substantial diagnostic value with low implementation cost and are sufficient for the current language scale.

## 104. Why the language syntax remains whitespace-oriented

Function calls do not use commas or mandatory parentheses:

```cara
CALL square 100 "red"
```

This matches the simple Logo-inspired command style of the DSL. Greedy expression parsing resolves arguments under the current grammar, while parentheses remain available to make nested calls explicit.

Changing to conventional `square(100, "red")` syntax would be a language redesign rather than an architectural improvement.

---

# Part XVII. Known Limits and Safe Future Extensions

## 105. Lexical extensions

Possible future work:

- identifiers containing digits after the first character;
- floating-point literals;
- comments;
- escaped string literals;
- unary minus.

These changes belong primarily to lexer/parser/grammar work.

## 106. Control-flow extensions

Possible additions:

- `ELSE`;
- richer comparisons such as `<=`, `>=`, `!=`;
- boolean expressions and logical operators;
- `WHILE`.

These would require coordinated parser, AST, semantic and interpreter changes.

## 107. Type-system extensions

Possible additions:

- explicit parameter types;
- function return types;
- boolean type;
- flow-sensitive type joins;
- constant evaluation;
- all-path return analysis.

The existing `ValueType` and semantic-scope architecture provides a natural place for such work, but these are not required for Carapace 1.0.0.

## 108. Scope extensions

Possible additions:

- explicit global assignment syntax;
- nested functions and closures;
- block-local scopes.

Each would materially change name-resolution semantics and should therefore be treated as a language design project, not a small patch.

## 109. Diagnostic extensions

Possible improvements:

- column positions;
- source spans;
- richer error rendering with source-line excerpts;
- multiple semantic diagnostics in one pass instead of fail-fast behavior.

## 110. Backend extensions

Because turtle calls are isolated, a future implementation could experiment with:

- SVG output;
- raster rendering;
- headless geometry tracing;
- alternative interactive graphics backends.

Such work could preserve most of the language front-end.

---

# Part XVIII. Thesis-Oriented Interpretation

## 111. What makes Carapace more than a command wrapper

At first glance, a turtle DSL can look like a thin mapping from keywords to `turtle.forward()` and similar functions. The architecture demonstrates substantially more:

- a formal lexical model;
- a recursive-descent parser;
- an explicit AST;
- semantic symbol tables;
- a multi-pass analyzer;
- lexical-scope rules;
- separate runtime environments;
- recursion;
- return values;
- lightweight static type reasoning;
- phase-specific error taxonomy;
- backend abstraction;
- a comprehensive executable specification in tests.

These elements make the project a genuine small programming-language implementation.

## 112. Suggested diploma chapter mapping

This guide can be transformed into thesis chapters roughly as follows.

### Chapter: Domain-specific languages and project motivation

Use:

- Sections 1–4;
- explanation of turtle graphics as the target domain;
- rationale for a small DSL rather than direct Python API use.

### Chapter: Language design

Use:

- Sections 5–16;
- grammar;
- commands, expressions, conditions, loops, functions and recursion;
- deliberate syntax restrictions.

### Chapter: Interpreter architecture

Use:

- Sections 17–22 and 60–71;
- full pipeline diagram;
- module responsibilities;
- AST role.

### Chapter: Semantic model

Use:

- Sections 23–31;
- multi-pass analyzer;
- symbol tables;
- `NUMBER` / `STRING` / `UNKNOWN`;
- static/runtime validation boundary.

### Chapter: Scope and functions

Use:

- Sections 32–38;
- global/function environments;
- shadowing;
- call stack vs scope chain;
- dynamic-scoping regression example.

### Chapter: Runtime implementation

Use:

- Sections 39–50;
- interpreter algorithm;
- function-call lifecycle;
- `ReturnSignal`;
- runtime validation;
- turtle adapter.

### Chapter: Error handling and testing

Use:

- Sections 51–59 and 81–89;
- error hierarchy;
- source locations;
- testing layers;
- regression and coverage results.

### Chapter: Evaluation and limitations

Use:

- Sections 94–110;
- design trade-offs;
- current non-goals;
- possible future work.

## 113. Strong technical points for an oral defense

If only a few design decisions can be discussed in depth, the strongest are:

1. **Parser vs semantic analyzer separation.** Explain why valid syntax can still have invalid meaning.
2. **AST as a stable intermediate representation.** Show how multiple later phases consume it.
3. **Multi-pass function collection.** Connect it to forward calls and recursion.
4. **Call stack vs lexical scope chain.** Use the `A`/`B`/global `x` example.
5. **Current-scope writes and local-over-global shadowing.** Explain why this prevents accidental global mutation.
6. **Semantic scopes vs runtime environments.** Explain symbols versus concrete values.
7. **`UNKNOWN` as deferred knowledge rather than an error.** Show static/runtime cooperation.
8. **Structural return capability plus runtime missing-return check.** Explain the trade-off against full path analysis.
9. **`ReturnSignal` as internal control flow.** Explain why it is not a language error.
10. **Turtle adapter and mocked tests.** Explain separation of logic from GUI side effects.
11. **Path-insensitive control-flow type merging.** Explain why uncertain blocks may degrade type knowledge to `UNKNOWN`.
12. **Executable tests as a language contract.** Give the 442-test regression result.

## 114. Questions a reviewer may ask

### “Why not detect every possible uninitialized variable statically?”

Because that requires path-sensitive definite-assignment analysis. Carapace intentionally detects obvious cases statically and leaves control-flow-dependent initialization to runtime.

### “Why can functions be called before they are declared?”

Function declarations are collected in an initial semantic pass and preloaded into the runtime global function registry. This also enables recursion and mutual recursion.

### “Why does a function not see the caller's local variables?”

Because caller-local visibility would implement dynamic scoping. Carapace uses a lexical model in which function locals fall back only to globals.

### “Why does `SET` inside a function not update a global with the same name?”

Writes are local to the current scope. This makes assignment predictable and allows explicit shadowing without accidental global mutation.

### “Why is `CALL maybe x` sometimes accepted semantically but able to fail at runtime?”

The analyzer only proves that the function contains at least one `RETURN`; it does not prove every control-flow path returns. Runtime checks the concrete path when a value is required.

### “Why is a function with no return allowed at all?”

Statement calls can represent drawing procedures. A returned value is required only in expression context.

### “Why is `UNKNOWN` useful?”

It represents insufficient static knowledge, especially for parameters and function-call results. It allows the analyzer to be conservative without rejecting valid dynamic programs.

### “Why are GUI errors not all converted into Carapace errors?”

Only expected user-value/backend errors are translated. Unexpected Python errors should remain distinguishable as implementation/system failures.

---

# Part XIX. Glossary

## 115. Core terms

**Abstract Syntax Tree (AST)**
A hierarchical representation of program structure produced by the parser and consumed by semantic analysis and interpretation.

**Arity**
The number of parameters expected by a function / arguments supplied by a call.

**Backend**
The external mechanism that performs graphics operations. In Carapace 1.0.0 this is Python `turtle`/Tk.

**Call stack**
The dynamic sequence of active function invocations and return points.

**Control flow**
The order in which statements execute, including conditional and repeated execution.

**Definite assignment**
Static analysis proving that a variable must have been assigned before a read on every possible path. Carapace does not implement full definite-assignment analysis.

**Domain-specific language (DSL)**
A language designed around a constrained problem domain rather than general-purpose programming. Carapace targets turtle graphics.

**Dynamic scoping**
A name-resolution model where a function can resolve names through caller environments. Carapace deliberately does not use this model.

**Environment**
A runtime mapping from variable names to concrete values, plus global function definitions in `GlobalEnvironment`.

**Expression**
A language construct that produces a value, such as a literal, variable, arithmetic operation or value-returning function call.

**Interpreter**
The runtime component that walks a validated AST and performs the behavior described by its nodes.

**Lexeme**
The concrete source text matched by a lexer rule, such as `FORWARD` or `100`.

**Lexer**
The front-end stage that converts characters into tokens.

**Lexical scope**
Name visibility determined by program structure rather than the dynamic caller chain. Carapace functions see their own locals and globals.

**Parser**
The stage that validates token structure against grammar and builds an AST.

**Recursion**
A function calling itself directly or indirectly.

**Runtime**
The phase in which concrete values exist and program statements actually execute.

**Scope**
A region/name namespace that determines where a variable can be declared and resolved.

**Semantic analysis**
Static validation performed after parsing but before execution: name resolution, arity checks, scope rules and lightweight type checks.

**Shadowing**
A local variable or parameter using the same name as a global variable and taking precedence for local reads.

**Statement**
A language construct executed for effect, such as `SET`, `FORWARD`, `IF`, `REPEAT` or a standalone function call.

**Symbol**
Static metadata representing a declared name during semantic analysis.

**Token**
A typed lexical unit emitted by the lexer.

**Type inference**
Deriving type knowledge from expressions without explicit annotations. Carapace performs lightweight local inference only.

**UNKNOWN**
A semantic type state meaning the value's type cannot be proven statically and must be validated at runtime when necessary.

---

# Part XX. Final Architectural Invariants

## 116. Invariants that define Carapace 1.0.0

The following statements are the shortest authoritative summary of the language architecture:

1. There is exactly one global runtime environment.
2. Every function invocation creates one fresh function runtime environment.
3. Every function environment's lexical parent is the global environment, never the caller environment.
4. `IF` and `REPEAT` do not create scopes.
5. `SET` writes into the current scope only.
6. Local variables and parameters may shadow globals.
7. Function definitions are global-only; nested functions are semantic errors.
8. All global functions are collected before function bodies and ordinary execution depend on them.
9. Forward function calls, direct recursion and mutual recursion are supported.
10. Function arguments are evaluated in the caller environment before switching environments.
11. Function callers' locals are not directly visible to callees.
12. Statement calls may complete without `RETURN`.
13. Expression calls require a concrete returned value.
14. `RETURN` carries an expression and is valid only inside a function.
15. `ReturnSignal` is internal control flow and is not a `CarapaceError`.
16. Semantic scopes contain symbols/type knowledge; runtime environments contain concrete values.
17. Static type knowledge consists of `NUMBER`, `STRING` and `UNKNOWN`.
18. Known type errors are rejected semantically; unknown values are validated at runtime.
19. The analyzer does not perform full path-sensitive definite-assignment or all-path return analysis.
20. Runtime environment restoration after a function call is guaranteed through `finally`.
21. Arithmetic is numeric only; division by zero is a Carapace runtime error.
22. `REPEAT`, `WIDTH`, `SPEED` and backend color values receive runtime constraint validation.
23. Source diagnostics carry line numbers; columns are outside version 1.0.0 scope.
24. Turtle graphics are isolated behind `commands.py`.
25. Core user-facing language failures derive from `CarapaceError`; unexpected system failures remain distinct.
26. The normal pipeline is Lexer → Parser → SemanticAnalyzer → Interpreter.
27. The AST is independent of parser implementation details and shared by later phases.
28. The test suite is an executable specification of these invariants.

---

# Conclusion

Carapace 1.0.0 is intentionally compact, but its implementation covers the essential architecture of a real interpreted language. Source code is tokenized, parsed into a dedicated AST, checked by a multi-pass semantic analyzer, executed against explicit runtime environments and finally mapped to turtle graphics through an isolated backend adapter.

The most important property of the project is not the number of commands. It is the consistency of the model across grammar, AST, semantic scopes, runtime environments, error handling and tests. Functions have a defined visibility model; `RETURN` has separate statement/expression semantics; type knowledge is explicitly divided between static and runtime phases; control-flow uncertainty is handled conservatively; and user-facing errors are classified by the stage that owns them.

That makes Carapace suitable both as a practical turtle-graphics DSL and as a compact case study of programming-language construction for a bachelor thesis.
