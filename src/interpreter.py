"""Runtime interpreter for semantically validated Carapace programs."""

from __future__ import annotations

from numbers import Real

import Carapace.src.commands as commands
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
from Carapace.src.environment import FunctionEnvironment, GlobalEnvironment
from Carapace.src.errors import ReturnSignal, RuntimeError
from Carapace.src.lexer import TokenType


_NO_RETURN = object()


class Interpreter:
    """Execute a Carapace AST using explicit global and function environments."""

    def __init__(self, tree: list[ASTNode], semantic_result):
        """Initialize runtime state from a validated AST and semantic result."""
        self.tree = tree
        self.semantic_result = semantic_result
        self.global_env = GlobalEnvironment()
        self.env = self.global_env

        # Semantic analysis has already validated and collected every global
        # function, so runtime registration is independent of source order.
        for name, symbol in semantic_result.functions.items():
            self.global_env.define_function(name, symbol.node)

    # ===================================================================
    # Program execution
    # ===================================================================

    def run(self):
        """Execute the program and preserve execution errors during cleanup."""
        commands.init_graphics()
        try:
            for node in self.tree:
                # Declarations were registered before execution.
                if isinstance(node, FunctionDefNode):
                    continue
                self.execute(node)
        except Exception:
            # Cleanup must never replace the original language/runtime error.
            try:
                commands.finish_graphics()
            except Exception:
                pass
            raise
        else:
            # With no primary error, a backend finalization failure remains an
            # internal/system failure and is allowed to propagate.
            commands.finish_graphics()

    # ===================================================================
    # Expression evaluation
    # ===================================================================

    def evaluate(self, node: ASTNode):
        """Evaluate an expression and return its runtime value."""
        match node:
            case LiteralNode(value=value):
                return value

            case VariableNode(name=name):
                try:
                    return self.env.get_variable(name)
                except RuntimeError as exc:
                    self._raise_runtime(node, str(exc))

            case BinOpNode(left=left, op=op, right=right):
                left_value = self.evaluate(left)
                right_value = self.evaluate(right)
                self._require_number(left_value, node, "Arithmetic operand")
                self._require_number(right_value, node, "Arithmetic operand")

                if op == TokenType.PLUS:
                    return left_value + right_value
                if op == TokenType.MINUS:
                    return left_value - right_value
                if op == TokenType.MULTIPLY:
                    return left_value * right_value
                if op == TokenType.DIVIDE:
                    if right_value == 0:
                        self._raise_runtime(node, "Division by zero")
                    return left_value / right_value

                self._raise_runtime(node, f"Unknown arithmetic operator: {op.name}")

            case FunctionCallNode(name=name, args=arguments):
                return self.execute_function_call(
                    function_name=name,
                    arguments=arguments,
                    value_required=True,
                    call_node=node,
                )

            case _:
                self._raise_runtime(
                    node,
                    f"Node {type(node).__name__} cannot be evaluated as an expression",
                )

    # ===================================================================
    # Statement execution
    # ===================================================================

    def execute(self, node: ASTNode):
        """Execute one statement node."""
        match node:
            case SetNode(name=name, value=value):
                self.env.set_variable(name, self.evaluate(value))

            case ForwardNode(distance=distance):
                value = self.evaluate(distance)
                self._require_number(value, node, "FORWARD")
                self._execute_command(commands.execute_forward, value, node=node)

            case BackwardNode(distance=distance):
                value = self.evaluate(distance)
                self._require_number(value, node, "BACKWARD")
                self._execute_command(commands.execute_backward, value, node=node)

            case LeftNode(angle=angle):
                value = self.evaluate(angle)
                self._require_number(value, node, "LEFT")
                self._execute_command(commands.execute_left, value, node=node)

            case RightNode(angle=angle):
                value = self.evaluate(angle)
                self._require_number(value, node, "RIGHT")
                self._execute_command(commands.execute_right, value, node=node)

            case RepeatNode(times=times, body=body):
                count = self.evaluate(times)
                self._require_repeat_count(count, node)
                for _ in range(count):
                    for child in body:
                        self.execute(child)

            case IfNode(left=left, op=op, right=right, body=body):
                if self._evaluate_comparison(left, op, right, node):
                    for child in body:
                        self.execute(child)

            case ColorNode(color_name=color):
                value = self.evaluate(color)
                self._require_string(value, node, "COLOR")
                self._execute_command(commands.execute_color, value, node=node)

            case WidthNode(size=size):
                value = self.evaluate(size)
                self._require_number(value, node, "WIDTH")
                if value <= 0:
                    self._raise_runtime(node, "WIDTH requires a positive number")
                self._execute_command(commands.execute_width, value, node=node)

            case SpeedNode(level=level):
                value = self.evaluate(level)
                self._require_number(value, node, "SPEED")
                if not isinstance(value, int) or isinstance(value, bool):
                    self._raise_runtime(node, "SPEED requires an integer from 0 to 10")
                if not 0 <= value <= 10:
                    self._raise_runtime(node, "SPEED requires an integer from 0 to 10")
                self._execute_command(commands.execute_speed, value, node=node)

            case PenUpNode():
                self._execute_command(commands.execute_penup, node=node)

            case PenDownNode():
                self._execute_command(commands.execute_pendown, node=node)

            case FunctionDefNode():
                # Function declarations have already been preloaded globally.
                return None

            case FunctionCallNode(name=name, args=arguments):
                return self.execute_function_call(
                    function_name=name,
                    arguments=arguments,
                    value_required=False,
                    call_node=node,
                )

            case ReturnNode(value=value):
                raise ReturnSignal(self.evaluate(value))

            case _:
                self._raise_runtime(node, f"Unsupported AST node {type(node).__name__}")

    # ===================================================================
    # Function calls
    # ===================================================================

    def execute_function_call(
        self,
        function_name: str,
        arguments: list[ASTNode],
        value_required: bool,
        call_node: ASTNode | None = None,
    ):
        """Execute one function call and optionally require a returned value."""
        try:
            function = self.global_env.get_function(function_name)
        except RuntimeError as exc:
            self._raise_runtime(call_node, str(exc))

        # Arguments are evaluated in the caller before the active environment
        # changes to the new function environment.
        evaluated_arguments = [self.evaluate(argument) for argument in arguments]

        if len(evaluated_arguments) != len(function.params):
            self._raise_runtime(
                call_node or function,
                f"Function '{function_name}' expects {len(function.params)} "
                f"arguments, got {len(evaluated_arguments)}",
            )

        function_env = FunctionEnvironment(parent=self.global_env)
        for parameter, value in zip(function.params, evaluated_arguments):
            function_env.set_variable(parameter, value)

        previous_env = self.env
        self.env = function_env
        returned = _NO_RETURN

        try:
            for child in function.body:
                self.execute(child)
        except ReturnSignal as signal:
            returned = signal.value
        finally:
            # Call-state restoration is independent from lexical scope lookup.
            self.env = previous_env

        if returned is _NO_RETURN:
            if value_required:
                self._raise_runtime(
                    call_node or function,
                    f"Function '{function_name}' did not return a value",
                )
            return None

        return returned

    # ===================================================================
    # Runtime validation helpers
    # ===================================================================

    @staticmethod
    def _is_number(value) -> bool:
        """Return whether ``value`` is a Carapace numeric runtime value."""
        return isinstance(value, Real) and not isinstance(value, bool)

    def _require_number(self, value, node: ASTNode, context: str) -> None:
        """Require a numeric runtime value for the given language context."""
        if not self._is_number(value):
            self._raise_runtime(
                node,
                f"{context} requires NUMBER, got {type(value).__name__.upper()}",
            )

    def _require_string(self, value, node: ASTNode, context: str) -> None:
        """Require a string runtime value for the given language context."""
        if not isinstance(value, str):
            self._raise_runtime(
                node,
                f"{context} requires STRING, got {type(value).__name__.upper()}",
            )

    def _require_repeat_count(self, value, node: ASTNode) -> None:
        """Validate the runtime constraints of a REPEAT iteration count."""
        self._require_number(value, node, "REPEAT")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            self._raise_runtime(node, "REPEAT requires a non-negative integer")

    def _evaluate_comparison(
        self,
        left_node: ASTNode,
        op: TokenType,
        right_node: ASTNode,
        node: ASTNode,
    ) -> bool:
        """Evaluate one comparison expression with runtime type checks."""
        left = self.evaluate(left_node)
        right = self.evaluate(right_node)

        if op == TokenType.EQ:
            if self._is_number(left) and self._is_number(right):
                return left == right
            if isinstance(left, str) and isinstance(right, str):
                return left == right
            self._raise_runtime(node, "Equality operands must have compatible scalar types")

        if op in (TokenType.LT, TokenType.GT):
            self._require_number(left, node, "Ordering comparison")
            self._require_number(right, node, "Ordering comparison")
            return left < right if op == TokenType.LT else left > right

        self._raise_runtime(node, f"Unknown comparison operator: {op.name}")

    def _execute_command(self, command, *args, node: ASTNode) -> None:
        """Translate expected turtle/user-value failures into Carapace RuntimeError."""
        try:
            command(*args)
        except (TypeError, ValueError) as exc:
            self._raise_runtime(node, str(exc))
        except Exception as exc:
            # Turtle uses TurtleGraphicsError for invalid colors and Tk may use
            # TclError for user-supplied backend values.  Do not broadly turn
            # unrelated implementation bugs into ordinary language errors.
            if exc.__class__.__name__ in {"TurtleGraphicsError", "TclError"}:
                self._raise_runtime(node, str(exc))
            raise

    def _raise_runtime(self, node: ASTNode | None, message: str):
        """Raise a Carapace runtime error enriched with source-line metadata."""
        if node is not None and getattr(node, "line", None) is not None:
            raise RuntimeError(f"Line {node.line}: {message}")
        raise RuntimeError(message)
