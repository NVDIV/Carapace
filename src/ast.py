"""Abstract Syntax Tree nodes for the Carapace language.

The AST is deliberately independent from the parser.  Parser code constructs
these nodes, while semantic analysis and interpretation consume them.
"""

from dataclasses import dataclass, field
from typing import Any

from Carapace.src.lexer import TokenType


@dataclass(kw_only=True)
class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    # Source locations are metadata rather than part of structural AST equality.
    # ``compare=False`` keeps tree-shape tests focused on language structure.
    line: int | None = field(default=None, compare=False)


@dataclass
class LiteralNode(ASTNode):
    """Represents a constant number or string value."""

    value: Any


@dataclass
class VariableNode(ASTNode):
    """Represents a variable reference by name."""

    name: str


@dataclass
class SetNode(ASTNode):
    """Represents ``SET <name> <expression>``."""

    name: str
    value: ASTNode


@dataclass
class BinOpNode(ASTNode):
    """Represents a binary arithmetic operation."""

    left: ASTNode
    op: TokenType
    right: ASTNode


@dataclass
class ForwardNode(ASTNode):
    """Represents forward turtle movement by an expression value."""

    distance: ASTNode


@dataclass
class BackwardNode(ASTNode):
    """Represents backward turtle movement by an expression value."""

    distance: ASTNode


@dataclass
class LeftNode(ASTNode):
    """Represents a left turtle rotation by an angle expression."""

    angle: ASTNode


@dataclass
class RightNode(ASTNode):
    """Represents a right turtle rotation by an angle expression."""

    angle: ASTNode


@dataclass
class RepeatNode(ASTNode):
    """Represents a repeated statement block."""

    times: ASTNode
    body: list[ASTNode]


@dataclass
class IfNode(ASTNode):
    """Represents a comparison-guarded statement block."""

    left: ASTNode
    op: TokenType
    right: ASTNode
    body: list[ASTNode]


@dataclass
class PenUpNode(ASTNode):
    """Represents lifting the drawing pen."""

    pass


@dataclass
class PenDownNode(ASTNode):
    """Represents lowering the drawing pen."""

    pass


@dataclass
class ColorNode(ASTNode):
    """Represents changing the drawing color."""

    color_name: ASTNode


@dataclass
class WidthNode(ASTNode):
    """Represents changing the drawing pen width."""

    size: ASTNode


@dataclass
class SpeedNode(ASTNode):
    """Represents changing turtle animation speed."""

    level: ASTNode


@dataclass
class FunctionDefNode(ASTNode):
    """Represents a global function declaration."""

    name: str
    params: list[str]
    body: list[ASTNode]


@dataclass
class FunctionCallNode(ASTNode):
    """Represents a function invocation and its argument expressions."""

    name: str
    args: list[ASTNode]


@dataclass
class ReturnNode(ASTNode):
    """Represents returning one expression value from a function."""

    value: ASTNode
