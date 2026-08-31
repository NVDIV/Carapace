"""Semantic analysis for the Carapace language.

The analyzer validates program meaning without executing user code.  It keeps
semantic symbols separate from runtime environments and deliberately performs
only lightweight type analysis: NUMBER, STRING and UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from Carapace.src.ast import (
    ASTNode,
    BackwardNode,
    BinOpNode,
    ColorNode,
    ForwardNode,
    FunctionCallNode,
    FunctionDefNode,
    IfNode,
    LeftNode,
    LiteralNode,
    PenDownNode,
    PenUpNode,
    RepeatNode,
    ReturnNode,
    RightNode,
    SetNode,
    SpeedNode,
    VariableNode,
    WidthNode,
)
from Carapace.src.errors import SemanticError
from Carapace.src.lexer import TokenType


class ValueType(Enum):
    """Static type knowledge available to the semantic analyzer."""

    NUMBER = auto()
    STRING = auto()
    UNKNOWN = auto()


@dataclass
class VariableSymbol:
    """A variable name known in a semantic scope."""

    name: str
    known_type: ValueType = ValueType.UNKNOWN
    line: int | None = None


@dataclass
class FunctionSymbol:
    """Metadata collected for a global function declaration."""

    name: str
    parameters: list[str]
    node: FunctionDefNode
    has_return_statement: bool
    line: int | None = None


@dataclass
class SemanticGlobalScope:
    """Global semantic namespace containing variables and functions."""

    variables: dict[str, VariableSymbol] = field(default_factory=dict)
    functions: dict[str, FunctionSymbol] = field(default_factory=dict)

    def get_variable(self, name: str) -> VariableSymbol | None:
        """Return a global variable symbol when it has been declared."""
        return self.variables.get(name)


@dataclass
class SemanticFunctionScope:
    """Function-local semantic scope whose only parent is the global scope."""

    parent: SemanticGlobalScope
    variables: dict[str, VariableSymbol] = field(default_factory=dict)

    def define_variable(
        self,
        name: str,
        known_type: ValueType = ValueType.UNKNOWN,
        line: int | None = None,
    ) -> None:
        """Create or replace one function-local variable symbol."""
        self.variables[name] = VariableSymbol(name, known_type, line)

    def get_variable(self, name: str) -> VariableSymbol | None:
        """Resolve a variable locally first and then in global scope."""
        return self.variables.get(name) or self.parent.get_variable(name)


@dataclass
class SemanticResult:
    """Validated semantic metadata consumed by later pipeline stages."""

    global_scope: SemanticGlobalScope

    @property
    def functions(self) -> dict[str, FunctionSymbol]:
        """Expose the validated function registry directly for convenience."""
        return self.global_scope.functions


class SemanticAnalyzer:
    """Perform multi-pass semantic validation of a parsed Carapace program."""

    def __init__(self, tree: list[ASTNode]):
        """Initialize semantic state for one parsed program."""
        self.tree = tree
        self.global_scope = SemanticGlobalScope()

    def analyze(self) -> SemanticResult:
        """Validate the complete AST and return semantic metadata."""
        self._collect_global_functions()
        self._analyze_top_level_statements()
        self._analyze_function_bodies()
        return SemanticResult(global_scope=self.global_scope)

    # ======================================================================
    # Pass 1: global declarations
    # ======================================================================

    def _collect_global_functions(self) -> None:
        """Collect every top-level function before any call is analyzed."""
        for node in self.tree:
            if not isinstance(node, FunctionDefNode):
                continue

            if node.name in self.global_scope.functions:
                self._error(node, f"Function '{node.name}' is already defined")

            self._validate_unique_parameters(node)
            self.global_scope.functions[node.name] = FunctionSymbol(
                name=node.name,
                parameters=list(node.params),
                node=node,
                has_return_statement=self._contains_return(node.body),
                line=node.line,
            )

    def _validate_unique_parameters(self, node: FunctionDefNode) -> None:
        """Reject duplicate parameter names within one function declaration."""
        seen: set[str] = set()
        for parameter in node.params:
            if parameter in seen:
                self._error(
                    node,
                    f"Function '{node.name}' has duplicate parameter '{parameter}'",
                )
            seen.add(parameter)

    def _contains_return(self, statements: list[ASTNode]) -> bool:
        """Structurally detect RETURN without performing path analysis."""
        for statement in statements:
            if isinstance(statement, ReturnNode):
                return True
            if isinstance(statement, (IfNode, RepeatNode)):
                if self._contains_return(statement.body):
                    return True
            # Nested FUNC is illegal and must not contribute RETURN metadata
            # to the enclosing function.
        return False

    # ======================================================================
    # Pass 2: top-level statements and global variables
    # ======================================================================

    def _analyze_top_level_statements(self) -> None:
        """Analyze non-function top-level statements in source order."""
        for node in self.tree:
            if isinstance(node, FunctionDefNode):
                continue
            self._analyze_statement(node, self.global_scope, in_function=False)

    # ======================================================================
    # Pass 3: function bodies
    # ======================================================================

    def _analyze_function_bodies(self) -> None:
        """Analyze each function using a fresh local scope over globals."""
        for symbol in self.global_scope.functions.values():
            scope = SemanticFunctionScope(parent=self.global_scope)
            for parameter in symbol.parameters:
                scope.define_variable(parameter, ValueType.UNKNOWN, symbol.line)

            for statement in symbol.node.body:
                self._analyze_statement(statement, scope, in_function=True)

    # ======================================================================
    # Statements
    # ======================================================================

    def _analyze_statement(
        self,
        node: ASTNode,
        scope: SemanticGlobalScope | SemanticFunctionScope,
        *,
        in_function: bool,
    ) -> None:
        """Analyze one statement in the supplied semantic scope."""
        match node:
            case SetNode(name=name, value=value):
                value_type = self._analyze_expression(value, scope)
                self._define_variable(scope, name, value_type, node.line)

            case ForwardNode(distance=value) | BackwardNode(distance=value):
                self._require_type(
                    self._analyze_expression(value, scope),
                    ValueType.NUMBER,
                    node,
                    "movement command",
                )

            case LeftNode(angle=value) | RightNode(angle=value):
                self._require_type(
                    self._analyze_expression(value, scope),
                    ValueType.NUMBER,
                    node,
                    "turn command",
                )

            case WidthNode(size=value):
                self._require_type(
                    self._analyze_expression(value, scope),
                    ValueType.NUMBER,
                    node,
                    "WIDTH",
                )

            case SpeedNode(level=value):
                self._require_type(
                    self._analyze_expression(value, scope),
                    ValueType.NUMBER,
                    node,
                    "SPEED",
                )

            case ColorNode(color_name=value):
                self._require_type(
                    self._analyze_expression(value, scope),
                    ValueType.STRING,
                    node,
                    "COLOR",
                )

            case PenUpNode() | PenDownNode():
                return

            case RepeatNode(times=times, body=body):
                self._require_type(
                    self._analyze_expression(times, scope),
                    ValueType.NUMBER,
                    node,
                    "REPEAT",
                )
                self._analyze_uncertain_block(body, scope, in_function=in_function)

            case IfNode(left=left, op=op, right=right, body=body):
                left_type = self._analyze_expression(left, scope)
                right_type = self._analyze_expression(right, scope)
                self._validate_comparison(left_type, op, right_type, node)
                self._analyze_uncertain_block(body, scope, in_function=in_function)

            case FunctionCallNode():
                self._analyze_function_call(node, scope, value_required=False)

            case FunctionDefNode():
                # The parser may structurally produce nested function nodes.
                # Semantic analysis owns the top-level-only restriction.
                self._error(node, "Nested function definitions are not allowed")

            case ReturnNode(value=value):
                if not in_function:
                    self._error(node, "RETURN is only valid inside a function")
                self._analyze_expression(value, scope)

            case _:
                self._error(node, f"Unsupported AST node {type(node).__name__}")


    def _analyze_uncertain_block(
        self,
        body: list[ASTNode],
        scope: SemanticGlobalScope | SemanticFunctionScope,
        *,
        in_function: bool,
    ) -> None:
        """Analyze IF/REPEAT without pretending the block must execute.

        Blocks do not create scopes, so assignments still introduce names into
        the enclosing scope.  However, an IF body may be skipped and a REPEAT
        body may execute zero times.  If such a block changes the known type of
        an already-known variable, the post-block type is therefore UNKNOWN.
        """
        before_types = {
            name: symbol.known_type for name, symbol in scope.variables.items()
        }

        for child in body:
            self._analyze_statement(child, scope, in_function=in_function)

        for name, previous_type in before_types.items():
            current = scope.variables.get(name)
            if current is not None and current.known_type != previous_type:
                current.known_type = ValueType.UNKNOWN

    # ======================================================================
    # Expressions
    # ======================================================================

    def _analyze_expression(
        self,
        node: ASTNode,
        scope: SemanticGlobalScope | SemanticFunctionScope,
    ) -> ValueType:
        """Analyze an expression and return the statically known value type."""
        match node:
            case LiteralNode(value=value):
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return ValueType.NUMBER
                if isinstance(value, str):
                    return ValueType.STRING
                return ValueType.UNKNOWN

            case VariableNode(name=name):
                symbol = scope.get_variable(name)
                if symbol is None:
                    self._error(node, f"Variable '{name}' is not defined")
                return symbol.known_type

            case BinOpNode(left=left, op=op, right=right):
                left_type = self._analyze_expression(left, scope)
                right_type = self._analyze_expression(right, scope)

                if op not in (
                    TokenType.PLUS,
                    TokenType.MINUS,
                    TokenType.MULTIPLY,
                    TokenType.DIVIDE,
                ):
                    self._error(node, f"Unsupported arithmetic operator {op.name}")

                if left_type == ValueType.STRING or right_type == ValueType.STRING:
                    self._error(node, "Arithmetic operators require numeric operands")

                if ValueType.UNKNOWN in (left_type, right_type):
                    return ValueType.UNKNOWN
                return ValueType.NUMBER

            case FunctionCallNode():
                self._analyze_function_call(node, scope, value_required=True)
                # Carapace deliberately performs no function return-type inference.
                return ValueType.UNKNOWN

            case _:
                self._error(node, f"Unsupported expression node {type(node).__name__}")

    def _analyze_function_call(
        self,
        node: FunctionCallNode,
        scope: SemanticGlobalScope | SemanticFunctionScope,
        *,
        value_required: bool,
    ) -> FunctionSymbol:
        """Validate function lookup, arity and expression-value requirements."""
        symbol = self.global_scope.functions.get(node.name)
        if symbol is None:
            self._error(node, f"Function '{node.name}' is not defined")

        for argument in node.args:
            self._analyze_expression(argument, scope)

        if len(node.args) != len(symbol.parameters):
            self._error(
                node,
                f"Function '{node.name}' expects {len(symbol.parameters)} "
                f"arguments, got {len(node.args)}",
            )

        if value_required and not symbol.has_return_statement:
            self._error(
                node,
                f"Function '{node.name}' cannot be used as an expression "
                "because it contains no RETURN statement",
            )

        return symbol

    # ======================================================================
    # Type and scope helpers
    # ======================================================================

    def _define_variable(
        self,
        scope: SemanticGlobalScope | SemanticFunctionScope,
        name: str,
        known_type: ValueType,
        line: int | None,
    ) -> None:
        """Define a variable symbol in the current semantic scope."""
        symbol = VariableSymbol(name=name, known_type=known_type, line=line)
        scope.variables[name] = symbol

    def _require_type(
        self,
        actual: ValueType,
        expected: ValueType,
        node: ASTNode,
        context: str,
    ) -> None:
        """Reject a statically known type incompatible with ``expected``."""
        # UNKNOWN is deliberately deferred to runtime validation.
        if actual not in (expected, ValueType.UNKNOWN):
            self._error(
                node,
                f"{context} requires {expected.name}, got {actual.name}",
            )

    def _validate_comparison(
        self,
        left: ValueType,
        op: TokenType,
        right: ValueType,
        node: ASTNode,
    ) -> None:
        """Validate statically known operand types for a comparison."""
        if ValueType.UNKNOWN in (left, right):
            return

        if op == TokenType.EQ:
            if left != right:
                self._error(node, "Equality operands must have compatible types")
            return

        if op in (TokenType.LT, TokenType.GT):
            if left != ValueType.NUMBER or right != ValueType.NUMBER:
                self._error(node, "Ordering comparisons require numeric operands")
            return

        self._error(node, f"Unsupported comparison operator {op.name}")

    def _error(self, node: ASTNode, message: str) -> None:
        """Raise ``SemanticError`` enriched with source-line metadata."""
        if node.line is not None:
            raise SemanticError(f"Line {node.line}: {message}")
        raise SemanticError(message)
