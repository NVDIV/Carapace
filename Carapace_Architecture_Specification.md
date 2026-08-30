# Carapace Language Architecture and Runtime Specification

## 1. Purpose and Scope

Carapace is a small interpreted domain-specific language for teaching fundamental programming concepts through turtle graphics.

The language is intentionally compact. Its design focuses on:

- readable syntax;
- explicit execution semantics;
- a small and understandable scope model;
- separation between lexical, syntactic, semantic, and runtime validation;
- deterministic function and variable resolution;
- clear user-facing errors;
- an implementation architecture suitable for explaining the complete interpreter pipeline in an educational context.

This document is the normative architecture and behavior specification of the Carapace implementation.

It defines:

- the complete source-processing pipeline;
- the responsibility of every module;
- the Abstract Syntax Tree model;
- variable and function scope semantics;
- function calls, recursion, and return behavior;
- semantic-analysis phases;
- static type knowledge and runtime validation;
- the runtime environment model;
- error categories and ownership;
- source-location propagation;
- the interaction between the interpreter and the turtle backend;
- language invariants that must remain true across the implementation.

---

# 2. High-Level Execution Pipeline

A Carapace program is processed through the following stages:

```text
source.cara
    ↓
Lexer
    ↓
Token stream
    ↓
Parser
    ↓
Abstract Syntax Tree
    ↓
Semantic Analyzer
    ↓
Validated AST + semantic metadata
    ↓
Interpreter
    ↓
Runtime environments
    ↓
Command adapter
    ↓
Python turtle backend
```

Each stage has one primary responsibility.

| Stage | Responsibility |
|---|---|
| Lexer | Convert source characters into tokens. |
| Parser | Convert tokens into a structurally valid AST. |
| Semantic Analyzer | Validate meaning that can be determined before execution. |
| Interpreter | Evaluate expressions and execute statements. |
| Runtime Environment | Store actual variable values and global function definitions during execution. |
| Command Adapter | Isolate the interpreter from the Python `turtle` implementation. |

A later stage may defensively validate assumptions made by an earlier stage, but it does not replace the earlier stage's responsibility.

For example:

- invalid syntax is a parser error, not a runtime error;
- duplicate functions are semantic errors, not interpreter errors;
- division by zero is a runtime error because it may depend on a value produced during execution.

---

# 3. Project Module Architecture

The source tree is organized as follows:

```text
src/
├── lexer.py
├── ast.py
├── parser.py
├── semantic_analyzer.py
├── environment.py
├── interpreter.py
├── commands.py
├── errors.py
└── main.py
```

---

## 3.1 `lexer.py`

`lexer.py` performs lexical analysis.

It defines:

- `TokenType`;
- `Token`;
- `Lexer`.

The lexer reads raw source text and produces a linear token stream.

A token contains:

```text
Token
├── type
├── value
└── source location
```

The source location contains at least a line number. A column number may also be stored when available.

The lexer recognizes:

- language keywords;
- identifiers;
- number literals;
- string literals;
- arithmetic operators;
- comparison operators;
- brackets;
- parentheses;
- end-of-file.

Keywords are case-insensitive.

Identifiers preserve the spelling written by the programmer.

The lexer does not perform:

- expression parsing;
- variable lookup;
- function lookup;
- scope validation;
- type checking;
- command execution.

An invalid character or malformed lexical construct produces `LexerError`.

---

## 3.2 `ast.py`

`ast.py` contains the language's Abstract Syntax Tree node definitions.

The AST is the shared representation used by:

- the Parser;
- the Semantic Analyzer;
- the Interpreter.

AST nodes contain structure, not execution state.

Typical node categories include:

```text
LiteralNode
VariableNode
BinOpNode
SetNode

ForwardNode
BackwardNode
LeftNode
RightNode
PenUpNode
PenDownNode
ColorNode
WidthNode
SpeedNode

RepeatNode
IfNode

FunctionDefNode
FunctionCallNode
ReturnNode
```

Every AST node that can produce a user-facing semantic or runtime error stores its source location.

Conceptually:

```text
ASTNode
└── location
    ├── line
    └── column
```

The AST does not contain:

- runtime variable values;
- runtime environments;
- turtle objects;
- call-stack frames.

---

## 3.3 `parser.py`

`parser.py` implements recursive-descent parsing.

Its responsibility is to determine whether the token stream has a valid grammatical structure and to construct the corresponding AST.

The parser understands:

- statements;
- arithmetic precedence;
- parentheses;
- blocks;
- loops;
- conditions;
- functions;
- function calls;
- return statements.

The parser does not decide whether a syntactically valid construct is semantically meaningful.

For example:

```cara
REPEAT "hello" [
    FORWARD 10
]
```

is structurally parseable because `"hello"` is an expression.

The Parser therefore creates a `RepeatNode`.

The Semantic Analyzer later rejects the string argument because `REPEAT` requires a numeric runtime value.

Similarly, a nested `FUNC` may be structurally parseable as a statement, but nested function definitions are rejected semantically.

A malformed expression, missing bracket, unexpected token, or other grammatical failure produces `ParserError`.

---

## 3.4 `semantic_analyzer.py`

`semantic_analyzer.py` validates program meaning before execution.

It defines the semantic symbol model and semantic scopes and performs multiple analysis phases.

It never executes user code.

It never calls turtle commands.

It never creates runtime environments.

Its responsibilities include:

- collecting global function declarations;
- allowing function calls before textual declaration;
- validating duplicate function declarations;
- validating duplicate parameters;
- rejecting nested function definitions;
- creating semantic scopes;
- validating function-call arity;
- validating `RETURN` context;
- checking statically known expression types;
- checking statically known command argument types;
- checking names when their invalidity can be determined statically;
- recording function metadata used by later stages.

---

## 3.5 `environment.py`

`environment.py` contains runtime environments.

It represents actual program state during execution.

There are exactly two environment classes:

```text
GlobalEnvironment
FunctionEnvironment
```

The architecture intentionally reflects the language semantics directly.

Detailed behavior is defined in the runtime-scope section of this document.

---

## 3.6 `interpreter.py`

`interpreter.py` executes a semantically validated AST.

Its responsibilities include:

- evaluating expressions;
- executing statements;
- managing the current runtime environment;
- creating function-call environments;
- evaluating function arguments;
- binding parameters;
- implementing recursion;
- handling `RETURN`;
- validating runtime-only constraints;
- converting execution failures into Carapace runtime errors.

The Interpreter does not define language grammar and does not build semantic symbol tables.

---

## 3.7 `commands.py`

`commands.py` is the boundary between Carapace and Python `turtle`.

The Interpreter does not directly depend on turtle-specific behavior beyond this adapter.

Typical operations include:

```text
init_graphics()
finish_graphics()

forward(distance)
backward(distance)
left(angle)
right(angle)

pen_up()
pen_down()

set_color(name)
set_width(width)
set_speed(speed)
```

This separation allows:

- interpreter tests without opening a GUI;
- command mocking;
- consistent translation of turtle/backend failures;
- isolation of Python/Tkinter implementation details.

---

## 3.8 `errors.py`

`errors.py` defines the public Carapace error hierarchy and internal control-flow exceptions.

```text
CarapaceError
├── SourceFileError
├── LexerError
├── ParserError
├── SemanticError
└── RuntimeError

ReturnSignal
```

`ReturnSignal` is not a `CarapaceError`.

It is an internal interpreter mechanism used to implement `RETURN`.

---

## 3.9 `main.py`

`main.py` is the CLI orchestration layer.

Its execution flow is:

```text
read CLI arguments
    ↓
read source file
    ↓
Lexer
    ↓
Parser
    ↓
Semantic Analyzer
    ↓
Interpreter
```

Diagnostic modes may stop the pipeline earlier.

For example:

```text
--tokens
```

prints tokens after lexical analysis.

```text
--ast
```

prints the syntactic AST after parsing.

Normal execution continues through semantic analysis and interpretation.

`main.py` catches `CarapaceError` and displays clean user-facing messages.

Unexpected Python exceptions are treated as internal system failures rather than ordinary Carapace program errors.

---

# 4. Language Scope Model

Carapace has two runtime scope categories:

1. one global scope for the entire program;
2. one fresh function-local scope for each active function call.

`IF` and `REPEAT` do not create scopes.

Blocks themselves do not create scopes.

Nested functions are not supported.

---

# 5. `GlobalEnvironment`

The program creates exactly one `GlobalEnvironment`.

Its structure is:

```text
GlobalEnvironment
├── variables
└── functions
```

Conceptually:

```python
GlobalEnvironment:
    variables: dict[str, RuntimeValue]
    functions: dict[str, FunctionDefNode]
```

The global environment stores:

- values assigned by top-level `SET`;
- every valid global function definition.

Global functions are registered before ordinary top-level execution begins.

This makes functions available regardless of their textual position in the source file.

---

# 6. `FunctionEnvironment`

Every function call creates a fresh `FunctionEnvironment`.

Its structure is:

```text
FunctionEnvironment
├── variables
└── parent → GlobalEnvironment
```

It contains:

- parameter values for the current call;
- variables created or assigned by `SET` during the call.

A `FunctionEnvironment` never stores functions.

Function lookup is always global.

A function environment always points directly to `GlobalEnvironment`.

It never points to the local environment of the calling function.

---

# 7. Variable Lookup

Variable lookup inside a function follows:

```text
current FunctionEnvironment
    ↓
GlobalEnvironment
```

Algorithmically:

```text
if name exists locally:
    return local value

else if name exists globally:
    return global value

else:
    runtime error
```

This is local-over-global lookup.

---

# 8. Assignment and Shadowing

`SET` always writes to the current environment.

It never searches parent environments to mutate an existing variable.

At top level:

```cara
SET x 10
```

writes:

```text
GlobalEnvironment.variables["x"] = 10
```

Inside a function:

```cara
FUNC demo [
    SET x 20
]
```

writes to that function call's local environment.

Therefore local-over-global shadowing is supported.

Example:

```cara
SET x 10

FUNC demo [
    SET x 20
    FORWARD x
]

CALL demo
FORWARD x
```

Inside `demo`, `x` is `20`.

After the function returns, global `x` is still `10`.

A local assignment never mutates the global variable with the same name.

---

# 9. `IF` and `REPEAT` Scope Semantics

`IF` and `REPEAT` execute in the current environment.

They do not create a new semantic or runtime scope.

Example:

```cara
SET x 1

REPEAT 1 [
    SET x 2
]

FORWARD x
```

After the loop:

```text
x == 2
```

At top level, `x` is global.

Inside a function, the same assignment changes the function-local `x`.

The same rule applies to `IF`.

---

# 10. Call Stack and Scope Chain Are Different Concepts

Carapace maintains a normal function call stack.

For example:

```text
main
 ↓
A
 ↓
B
 ↓
C
```

This represents execution order.

It does not represent name visibility.

If `A` calls `B`, and `B` calls `C`:

```text
A_environment.parent = GlobalEnvironment
B_environment.parent = GlobalEnvironment
C_environment.parent = GlobalEnvironment
```

Not:

```text
C → B → A → global
```

Therefore a callee cannot access caller-local variables.

Example:

```cara
FUNC B [
    FORWARD x
]

FUNC A [
    SET x 100
    CALL B
]

CALL A
```

`B` does not see `A`'s local `x`.

`B` searches:

```text
B local variables
    ↓
global variables
```

If no global `x` exists, reading `x` fails.

This prevents dynamic scoping.

---

# 11. Function Declaration Semantics

Functions are global declarations.

A valid function definition exists only at program top level.

Example:

```cara
FUNC square size [
    ...
]
```

is valid.

A function definition inside another function, `IF`, or `REPEAT` is invalid:

```cara
FUNC outer [
    FUNC inner [
        FORWARD 10
    ]
]
```

This produces `SemanticError`.

Carapace does not support:

- nested functions;
- closures;
- captured local environments.

---

# 12. Function Declaration Collection

Global function declarations are collected before body analysis and before program execution.

Therefore:

```cara
CALL draw

FUNC draw [
    FORWARD 100
]
```

is valid.

The function does not need to appear before its call in source order.

The same mechanism supports:

- direct recursion;
- mutual recursion.

For example:

```cara
FUNC A [
    CALL B
]

FUNC B [
    CALL A
]
```

both names are known before either body is semantically analyzed.

---

# 13. Function Parameters

Function parameters are local to a function call.

Example:

```cara
FUNC move distance [
    FORWARD distance
]
```

During:

```cara
CALL move 100
```

the call creates:

```text
FunctionEnvironment
└── variables
    └── distance = 100
```

Parameters are inserted before the body executes.

Duplicate parameter names are invalid:

```cara
FUNC test x x [
    ...
]
```

This produces `SemanticError`.

Parameter types are not declared in Carapace.

The Semantic Analyzer therefore treats their static type as unknown unless it can safely derive more information from local expressions.

---

# 14. Function Calls

A function may be called in two semantic contexts.

## 14.1 Statement context

```cara
CALL draw
```

The call is executed for its side effects.

A returned value, if any, is discarded.

A statement-position call is allowed to finish without executing `RETURN`.

This supports procedure-like functions.

---

## 14.2 Expression context

A `FunctionCallNode` is also a valid expression factor.

For example:

```cara
SET result CALL square 5
```

The call must produce a runtime value.

If the function reaches the end of the executed path without `RETURN`, the Interpreter raises `RuntimeError`.

---

# 15. Function Call Argument Parsing

A function call has the form:

```text
CALL <Identifier> <Expression>*
```

Arguments are parsed from left to right.

The parser repeatedly parses a complete `Expression` while the next token can begin an argument expression.

Because each argument is parsed as a complete expression:

```cara
CALL square 10 + 5
```

contains one argument:

```text
10 + 5
```

not:

```text
(CALL square 10) + 5
```

To use a call as part of a larger expression, parentheses make the grouping explicit:

```cara
(CALL square 10) + 5
```

Multiple adjacent expression starts form multiple arguments:

```cara
CALL foo 10 20
```

contains two arguments.

A nested call can be used as an argument where the parser can unambiguously recognize it as an expression. Parentheses are the explicit and recommended form:

```cara
CALL outer (CALL inner 10)
```

This preserves the current lightweight call syntax without introducing commas or mandatory call parentheses.

---

# 16. Recursion

Recursion is supported.

Each recursive call creates a new `FunctionEnvironment`.

Example:

```cara
FUNC countdown n [
    IF n > 0 [
        CALL countdown n - 1
    ]
]
```

Calling:

```cara
CALL countdown 3
```

creates independent runtime environments:

```text
countdown call: n = 3
countdown call: n = 2
countdown call: n = 1
countdown call: n = 0
```

Every environment points directly to the same `GlobalEnvironment`.

Therefore parameter and local-variable values from separate recursive calls cannot overwrite each other.

---

# 17. Environment Restoration

The Interpreter stores the currently active variable environment.

During a function call:

```text
previous environment
    ↓
new FunctionEnvironment
```

The previous environment is always restored when the call ends.

The restoration happens even if:

- the function executes `RETURN`;
- a nested call returns;
- a runtime error occurs.

Conceptually:

```python
previous_env = current_env
current_env = function_env

try:
    execute_function_body()
finally:
    current_env = previous_env
```

For nested calls:

```text
global
  ↓
A
  ↓
B
  ↓
C
```

the current interpreter environment changes with execution:

```text
global → A → B → C → B → A → global
```

This sequence is call-state restoration.

It does not change the scope-parent rule:

```text
A.parent = global
B.parent = global
C.parent = global
```

---

# 18. `RETURN`

`RETURN` has the form:

```text
RETURN <Expression>
```

A bare `RETURN` is not part of the language.

`RETURN` is valid only inside a function.

Example:

```cara
RETURN 10
```

at program top level produces `SemanticError`.

---

# 19. Runtime Implementation of `RETURN`

The Interpreter implements `RETURN` using an internal `ReturnSignal`.

Conceptually:

```python
RETURN expression
    ↓
evaluate expression
    ↓
raise ReturnSignal(value)
```

The active function-call handler catches the signal:

```python
except ReturnSignal as signal:
    return signal.value
```

`ReturnSignal` is not an error.

It is an internal control-flow mechanism.

It may pass through nested `IF` and `REPEAT` execution until it reaches the active function-call boundary.

Therefore:

```cara
FUNC test [
    REPEAT 10 [
        IF condition > 0 [
            RETURN 42
        ]
    ]
]
```

returns from the entire function, not merely from the inner block.

---

# 20. Return Analysis Policy

Carapace intentionally does not implement full return-path analysis or return-type inference.

The Semantic Analyzer does not attempt to prove that every possible control-flow path returns.

It also does not infer a static function return type.

Example:

```cara
FUNC maybe x [
    IF x > 0 [
        RETURN x
    ]
]
```

The function contains a `RETURN`, but not every runtime path executes it.

The semantic metadata for the function records:

```text
has_return_statement = true
```

This means only that the body structurally contains at least one `RETURN`.

It is not a guarantee that every invocation returns.

---

# 21. Calls Requiring a Return Value

When a function is used as an expression, Carapace applies two levels of validation.

## 21.1 Semantic validation

If the target function contains no `RETURN` statement anywhere in its body, expression use is invalid.

Example:

```cara
FUNC draw [
    FORWARD 100
]

SET x CALL draw
```

This produces `SemanticError`.

The analyzer can prove that the function has no value-producing path at all.

---

## 21.2 Runtime validation

If the function contains at least one `RETURN`, expression use is semantically allowed.

Example:

```cara
FUNC maybe x [
    IF x > 0 [
        RETURN x
    ]
]
```

This call succeeds:

```cara
SET x CALL maybe 10
```

This call reaches the end without executing `RETURN`:

```cara
SET x CALL maybe -10
```

and produces `RuntimeError`.

This deliberately avoids complex control-flow analysis.

---

# 22. Semantic Scope Model

Semantic scopes are separate from runtime environments.

They exist only during semantic analysis.

They store symbols and metadata, not runtime values.

The semantic scope model mirrors runtime visibility:

```text
SemanticGlobalScope
├── global variable symbols
└── function symbols

SemanticFunctionScope
├── parameter symbols
├── local variable symbols
└── parent → SemanticGlobalScope
```

`IF` and `REPEAT` do not create semantic scopes.

---

# 23. Semantic Symbols

A minimal semantic model contains the following conceptual symbol types.

```text
VariableSymbol
├── name
├── known_type
└── source location
```

```text
FunctionSymbol
├── name
├── parameters
├── FunctionDefNode
├── has_return_statement
└── source location
```

Known value types are:

```text
NUMBER
STRING
UNKNOWN
```

`UNKNOWN` means that the analyzer cannot safely determine the runtime type without executing the program.

It is not an error.

---

# 24. Semantic Analysis Phases

Semantic analysis is performed in multiple phases.

---

## 24.1 Phase 1 — Collect Global Function Declarations

The analyzer scans direct children of the program AST and registers all `FunctionDefNode` objects.

This happens before function bodies or ordinary statements are analyzed.

This provides:

- forward function calls;
- recursion;
- mutual recursion.

---

## 24.2 Phase 2 — Validate Function Declarations

The analyzer validates the global function table.

It detects:

- duplicate function names;
- duplicate parameter names;
- invalid nested function definitions.

It also computes lightweight function metadata such as:

```text
has_return_statement
```

---

## 24.3 Phase 3 — Analyze Top-Level Statements

Non-function top-level statements are analyzed in source order.

Top-level `SET` introduces or updates a global variable symbol.

Direct top-level use before a known declaration can therefore be rejected.

Example:

```cara
FORWARD x
SET x 100
```

`FORWARD x` is a semantic error because `x` is not known at that point in sequential top-level analysis.

Runtime variable values are still created only when `SET` actually executes.

---

## 24.4 Phase 4 — Analyze Function Bodies

After global top-level symbols have been collected through semantic analysis, every function body is analyzed using a fresh `SemanticFunctionScope`.

The scope initially contains the function parameters.

Its parent is `SemanticGlobalScope`.

Local `SET` statements introduce or update local symbols.

A function body can therefore resolve:

```text
local parameter / local variable
    ↓
global variable
```

and all functions through the global function table.

---

## 24.5 Phase 5 — Final Consistency Validation

The analyzer may perform lightweight final checks over collected metadata.

It does not execute code and does not simulate every control-flow path.

---

# 25. Global Variable Symbols vs Runtime Initialization

A semantic declaration and a runtime value are different concepts.

Consider:

```cara
CALL draw

SET size 100

FUNC draw [
    FORWARD size
]
```

After top-level semantic analysis, `size` is a known global symbol.

Therefore the function body can resolve the name semantically.

At runtime, however, execution begins with:

```cara
CALL draw
```

before:

```cara
SET size 100
```

has executed.

The runtime `GlobalEnvironment` therefore does not yet contain a value for `size`.

The function call fails with `RuntimeError`.

This distinction is intentional:

```text
Semantic scope:
"Does this program define this name?"

Runtime environment:
"Does this name currently have a value on this execution path?"
```

---

# 26. Local Variables and Control Flow

`SET` inside `IF` or `REPEAT` introduces a variable in the enclosing semantic scope because blocks do not create scopes.

Example:

```cara
FUNC test x [
    IF x > 0 [
        SET y 10
    ]

    FORWARD y
]
```

The semantic analyzer knows that `y` is a local symbol.

It does not prove that the `IF` condition is true.

If execution reaches `FORWARD y` without the assignment running, runtime lookup fails.

Carapace intentionally does not perform path-sensitive definite-assignment analysis.

---

# 27. Lightweight Static Type Knowledge

Carapace is dynamically executed but uses limited static type knowledge during semantic analysis.

The analyzer can identify:

```text
10        → NUMBER
"red"     → STRING
parameter → UNKNOWN
CALL ...  → UNKNOWN
```

A variable may have a known type when it follows directly from a statically known assignment.

If control flow or function calls make the type uncertain, the analyzer uses `UNKNOWN`.

It never guesses.

---

# 28. Arithmetic Type Rules

Arithmetic operators operate on numbers.

```text
+  NUMBER × NUMBER → NUMBER
-  NUMBER × NUMBER → NUMBER
*  NUMBER × NUMBER → NUMBER
/  NUMBER × NUMBER → NUMBER
```

String concatenation is not implicitly provided by `+`.

Examples:

```cara
SET x 10 + 20
```

is valid.

```cara
SET x 10 + "red"
```

produces `SemanticError` because both operand types are statically known and incompatible.

If one operand has type `UNKNOWN`, final validation is deferred until runtime.

Division by zero is a runtime error because the denominator may be produced dynamically.

---

# 29. Command Type Rules

The following command argument types are part of the language semantics.

| Construct | Required type |
|---|---|
| `FORWARD expression` | NUMBER |
| `BACKWARD expression` | NUMBER |
| `LEFT expression` | NUMBER |
| `RIGHT expression` | NUMBER |
| `WIDTH expression` | NUMBER |
| `SPEED expression` | NUMBER |
| `REPEAT expression [...]` | NUMBER |
| `COLOR expression` | STRING |
| `PENUP` | no argument |
| `PENDOWN` | no argument |

If the argument type is statically known and invalid, the Semantic Analyzer rejects it.

If its type is `UNKNOWN`, the Interpreter validates the concrete runtime value.

---

# 30. Runtime Value Constraints

Some constraints depend on the actual value, not only its type.

They are checked by the Interpreter.

Examples include:

### `REPEAT`

The repeat count must be a non-negative integer.

The Interpreter does not silently convert arbitrary floating-point values using `int()`.

Invalid examples include:

```text
-1
2.5
```

### `WIDTH`

The value must be valid for the drawing backend and satisfy the Carapace width rules.

### `SPEED`

The value must satisfy the supported Carapace speed range.

The target runtime model uses the turtle-compatible numeric range:

```text
0..10
```

### `COLOR`

The expression must produce a string.

The resulting color name must also be accepted by the turtle backend.

An unknown color string is therefore a runtime error.

---

# 31. Comparison Semantics

`IF` uses explicit comparison operators.

Supported operators are:

```text
==
<
>
```

Rules:

### Equality

```text
==
```

may compare compatible scalar values.

When both static types are known and different, the analyzer rejects the comparison.

### Ordering

```text
<
>
```

require numeric operands.

If operand types are unknown until execution, validation is deferred to the Interpreter.

---

# 32. Undefined Variables

Undefined-variable handling is split between semantic analysis and runtime execution.

The Semantic Analyzer reports an undefined variable when the invalid reference is statically determinable.

The Interpreter reports a runtime undefined-variable error when a symbol is semantically known but has not received a runtime value on the executed path.

Examples:

```cara
FORWARD never_defined
```

is a semantic error when no valid symbol exists.

By contrast:

```cara
IF x > 0 [
    SET y 10
]

FORWARD y
```

may become a runtime error when the branch does not execute.

---

# 33. Undefined Functions

Function existence is fully known after global declaration collection.

Therefore:

```cara
CALL missing_function
```

always produces `SemanticError`.

Function lookup failure is not an ordinary runtime-language situation after successful semantic analysis.

The Interpreter may still contain defensive checks to protect internal invariants.

---

# 34. Function Arity

The number of function parameters is known statically.

Therefore an incorrect argument count is a semantic error.

Example:

```cara
FUNC move distance [
    FORWARD distance
]

CALL move 10 20
```

produces `SemanticError`.

Argument expressions themselves are still evaluated at runtime after semantic validation.

---

# 35. Runtime Function Execution Algorithm

A function call is executed as follows.

```text
1. Resolve FunctionDefNode from GlobalEnvironment.
2. Evaluate argument expressions in the caller's current environment.
3. Verify argument count defensively.
4. Create FunctionEnvironment(parent = GlobalEnvironment).
5. Bind parameter names to argument values.
6. Save the current interpreter environment.
7. Make the new FunctionEnvironment current.
8. Execute the function body.
9. If ReturnSignal occurs:
       extract the returned value.
10. If the body finishes normally:
       no value was returned.
11. Restore the previous current environment in finally.
12. If the call occurred in expression context and no value was returned:
       raise RuntimeError.
13. Otherwise return the value or complete the statement call.
```

---

# 36. Semantic Result

Successful semantic analysis produces the validated AST together with semantic metadata.

Conceptually:

```text
SemanticResult
├── global_scope
└── functions
    └── FunctionSymbol metadata
```

The Interpreter uses the validated global function registry to populate:

```text
GlobalEnvironment.functions
```

before ordinary program execution.

Semantic variable symbols are not copied as runtime values.

Runtime variables are created only by actual `SET` execution and parameter binding.

---

# 37. Function Definition at Runtime

Because function declarations are collected before execution, `FunctionDefNode` does not depend on reaching its textual position during normal execution.

Before executing ordinary statements:

```text
GlobalEnvironment.functions
```

is populated with all validated top-level function definitions.

Therefore:

```cara
CALL draw

FUNC draw [
    FORWARD 100
]
```

works even though the call appears first.

A top-level `FunctionDefNode` encountered in the sequential AST does not redeclare or overwrite the function during execution.

---

# 38. Error Model

Carapace errors are classified by the stage that owns the failure.

```text
CarapaceError
├── SourceFileError
├── LexerError
├── ParserError
├── SemanticError
└── RuntimeError
```

This classification is visible to the user through consistent messages.

---

# 39. `SourceFileError`

`SourceFileError` occurs before language processing.

Examples include:

- source file does not exist;
- source file cannot be read;
- invalid source-file extension when extension validation is enabled.

It is not a semantic or runtime language error.

---

# 40. `LexerError`

`LexerError` means the source cannot be converted into a valid token stream.

Examples:

- unknown character;
- malformed lexical construct;
- invalid string tokenization.

The error includes source location.

---

# 41. `ParserError`

`ParserError` means the token sequence violates the grammar.

Examples:

- missing `]`;
- missing `)`;
- unexpected token;
- invalid expression structure;
- missing required command argument;
- malformed function syntax.

Parser errors concern structure only.

---

# 42. `SemanticError`

`SemanticError` means the program is syntactically valid but violates a rule that can be determined without executing the program.

Examples include:

- duplicate function declaration;
- duplicate parameter;
- nested function definition;
- undefined function;
- wrong function argument count;
- `RETURN` outside a function;
- function with no `RETURN` used as an expression;
- statically known invalid arithmetic operand types;
- statically known invalid command argument type;
- statically determinable undefined variable;
- invalid comparison of statically known incompatible values.

---

# 43. `RuntimeError`

`RuntimeError` means the program passed parsing and semantic analysis, but the concrete execution path or runtime values violate a language rule.

Examples include:

- division by zero;
- semantically known variable not initialized on the executed path;
- `UNKNOWN` expression evaluates to the wrong runtime type;
- invalid `REPEAT` value;
- invalid runtime `WIDTH` or `SPEED` value;
- invalid turtle color;
- value-required function call reaches the end without executing `RETURN`.

Runtime errors are Carapace user-program errors.

They are not raw Python exceptions.

---

# 44. `ReturnSignal`

`ReturnSignal` is internal control flow.

It carries:

```text
returned runtime value
```

It is never shown to the user.

It is caught by the active function-call boundary.

It is not part of the public error hierarchy.

---

# 45. Internal System Errors

Unexpected implementation failures are not converted into ordinary Carapace errors unless they correspond to a known user-program condition.

Examples may include:

- violated internal invariants;
- unexpected Python `AttributeError`;
- accidental implementation `KeyError`;
- graphics subsystem initialization failure unrelated to the Carapace program.

`main.py` handles these as internal system errors.

This distinction prevents interpreter bugs from being mislabeled as user mistakes.

---

# 46. Source Locations and Error Messages

Every public language error should include a useful source location whenever possible.

Preferred form:

```text
Line 12: Undefined variable 'distance'
```

or, when columns are available:

```text
Line 12, column 9: Undefined variable 'distance'
```

Source locations originate in lexer tokens and are propagated into AST nodes.

The Semantic Analyzer and Interpreter report the location of the AST construct responsible for the failure.

Examples:

```text
Line 7: Function 'square' expects 1 argument, got 2
Line 4: REPEAT expects a non-negative integer, got -2
Line 18: Function 'maybe' did not return a value on this execution path
```

---

# 47. Turtle Backend Errors

Python turtle and Tkinter implementation details are not exposed as normal Carapace errors.

For example, an invalid color may cause an internal turtle/Tkinter exception.

Carapace converts the user-caused failure into:

```text
RuntimeError: Invalid color 'bluue'
```

rather than exposing a Python traceback such as:

```text
_tkinter.TclError
```

Backend failures not caused by the Carapace program remain internal/system errors.

---

# 48. Runtime Initialization and Finalization

Graphics initialization occurs only after:

- lexing succeeds;
- parsing succeeds;
- semantic analysis succeeds.

This prevents a turtle window from opening for programs that cannot be executed.

The graphics backend is finalized in a controlled way after interpretation.

Runtime cleanup must not destroy the original Carapace error when execution fails.

---

# 49. Language Grammar Model

The core grammar is conceptually:

```ebnf
<Program>          ::= <Statement>* EOF

<Statement>        ::= <Command>
                     | <Loop>
                     | <Assignment>
                     | <IfStatement>
                     | <FunctionDef>
                     | <FunctionCall>
                     | <ReturnStatement>

<FunctionDef>      ::= "FUNC" <Identifier> <Identifier>* "[" <Statement>* "]"

<FunctionCall>     ::= "CALL" <Identifier> <Expression>*

<ReturnStatement>  ::= "RETURN" <Expression>

<IfStatement>      ::= "IF" <Expression> <ComparisonOp> <Expression>
                       "[" <Statement>* "]"

<ComparisonOp>     ::= "==" | "<" | ">"

<Assignment>       ::= "SET" <Identifier> <Expression>

<Command>          ::= "FORWARD" <Expression>
                     | "BACKWARD" <Expression>
                     | "LEFT" <Expression>
                     | "RIGHT" <Expression>
                     | "PENUP"
                     | "PENDOWN"
                     | "COLOR" <Expression>
                     | "WIDTH" <Expression>
                     | "SPEED" <Expression>

<Loop>             ::= "REPEAT" <Expression> "[" <Statement>* "]"

<Expression>       ::= <Term> (("+" | "-") <Term>)*

<Term>             ::= <Factor> (("*" | "/") <Factor>)*

<Factor>           ::= <Number>
                     | <String>
                     | <Identifier>
                     | "(" <Expression> ")"
                     | <FunctionCall>
```

Semantic restrictions are intentionally not encoded into this context-free grammar.

For example:

```cara
FORWARD "hello"
```

can be syntactically valid and semantically invalid.

This separation keeps grammar responsible for structure and semantic analysis responsible for meaning.

---

# 50. Architectural Invariants

The following rules are invariants of the implementation.

1. Exactly one `GlobalEnvironment` exists per program execution.
2. Every active function call owns a distinct `FunctionEnvironment`.
3. Every `FunctionEnvironment` points directly to `GlobalEnvironment`.
4. A `FunctionEnvironment` never points to another function environment.
5. Functions exist only in `GlobalEnvironment`.
6. Functions are top-level only.
7. All functions are collected before execution.
8. Function textual order does not determine visibility.
9. `SET` always writes into the current environment.
10. Function-local variables shadow globals with the same name.
11. Function-local assignments do not mutate global variables.
12. Variable lookup is local-first, global-second.
13. Caller-local variables are invisible to callees.
14. `IF` does not create a scope.
15. `REPEAT` does not create a scope.
16. Function calls restore the previous current environment even on `RETURN` or error.
17. Direct recursion is supported.
18. Mutual recursion is supported.
19. Semantic scopes and runtime environments are separate structures.
20. The Semantic Analyzer never executes user code.
21. Function return types are not statically inferred.
22. Full all-path return analysis is not performed.
23. `RETURN` always contains an expression.
24. `RETURN` outside a function is a semantic error.
25. A statement-position function call may finish without returning a value.
26. An expression-position function call must produce a runtime value.
27. A function with no `RETURN` anywhere cannot be used as an expression.
28. A function containing `RETURN` may still fail at runtime if the executed path does not reach it.
29. Statically provable type errors are semantic errors.
30. Execution-dependent type/value errors are runtime errors.
31. Ordinary Carapace mistakes do not expose raw Python or Tkinter exceptions.
32. Every user-facing error carries source location when available.

---

# 51. Deliberate Non-Goals

The architecture deliberately does not include:

- nested functions;
- closures;
- dynamic scoping;
- block-local scopes;
- a `global` declaration;
- mutation of parent variables through `SET`;
- static function parameter types;
- full return-type inference;
- full control-flow analysis;
- all-path return proof;
- path-sensitive definite-assignment analysis;
- advanced static type inference.

These omissions are intentional.

They keep the language small enough to be understandable while still demonstrating the complete architecture of a real interpreter:

```text
lexical analysis
→ parsing
→ AST
→ semantic analysis
→ runtime environments
→ interpretation
→ controlled error handling
```

---

# 52. Complete Architectural Summary

The static side of Carapace is:

```text
Source
  ↓
Lexer
  ↓
Tokens
  ↓
Parser
  ↓
AST
  ↓
SemanticAnalyzer
  ├── SemanticGlobalScope
  │   ├── global variable symbols
  │   └── global function symbols
  │
  └── SemanticFunctionScope
      ├── parameters
      ├── local variable symbols
      └── parent → SemanticGlobalScope
```

The runtime side is:

```text
Interpreter
  │
  ├── GlobalEnvironment
  │   ├── global variable values
  │   └── global function definitions
  │
  └── FunctionEnvironment
      ├── parameter values
      ├── local variable values
      └── parent → GlobalEnvironment
```

The call stack records active execution:

```text
main → A → B → C
```

but scope lookup remains:

```text
A → global
B → global
C → global
```

This gives Carapace a deliberately simple and consistent programming model:

- global functions;
- global and function-local variables;
- local-over-global shadowing;
- no dynamic scoping;
- no block scopes;
- recursion with independent call environments;
- semantic validation before execution;
- runtime checks only where actual values or execution paths are required;
- a clear error boundary at every stage of the interpreter pipeline.
