import pytest

from Carapace.src.lexer import TokenType
from Carapace.src.ast import (
    SetNode, LiteralNode, VariableNode, BinOpNode, ForwardNode, BackwardNode, LeftNode, RightNode, PenUpNode, PenDownNode, ColorNode, WidthNode, SpeedNode,
)
from Carapace.src.errors import ParserError

from Carapace.tests.conftest import parse, parse_one


# ===========================================================================
# SET
# ===========================================================================


# ---------------------------------------------------------------------------
# Basic assignments
# ---------------------------------------------------------------------------

def test_set_assigns_number():
    """SET assigns a numeric literal to a variable."""
    result = parse_one("SET x 10")

    assert result == SetNode(
        name="x",
        value=LiteralNode(10),
    )


def test_set_assigns_string():
    """SET assigns a string literal to a variable."""
    result = parse_one('SET col "red"')

    assert result == SetNode(
        name="col",
        value=LiteralNode("red"),
    )


def test_set_assigns_variable():
    """SET can assign the value of another variable."""
    result = parse_one("SET x y")

    assert result == SetNode(
        name="x",
        value=VariableNode("y"),
    )


# ---------------------------------------------------------------------------
# SET expressions
# ---------------------------------------------------------------------------

def test_set_assigns_arithmetic_expression():
    """SET accepts an arithmetic expression as its value."""
    result = parse_one("SET x 10 + 20")

    assert result == SetNode(
        name="x",
        value=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
    )


def test_set_preserves_expression_precedence():
    """SET preserves arithmetic precedence inside its assigned expression."""
    result = parse_one("SET x 10 + 20 * 3")

    assert result.value == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=BinOpNode(
            left=LiteralNode(20),
            op=TokenType.MULTIPLY,
            right=LiteralNode(3),
        ),
    )


# ---------------------------------------------------------------------------
# SET errors
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source",
    [
        "SET",
        "SET 10 20",
        "SET x",
        "SET x + 10",
    ],
)
def test_set_rejects_invalid_syntax(source):
    """SET requires an identifier followed by an expression."""
    with pytest.raises(ParserError):
        parse(source)


# ===========================================================================
# Movement commands
# ===========================================================================


# ---------------------------------------------------------------------------
# Literal arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source,expected",
    [
        ("FORWARD 100", ForwardNode(LiteralNode(100))),
        ("BACKWARD 100", BackwardNode(LiteralNode(100))),
        ("LEFT 90", LeftNode(LiteralNode(90))),
        ("RIGHT 90", RightNode(LiteralNode(90))),
    ],
)
def test_movement_command_accepts_literal(source, expected):
    """Movement commands accept numeric literal arguments."""
    assert parse_one(source) == expected


# ---------------------------------------------------------------------------
# Variable arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source,expected",
    [
        ("FORWARD x", ForwardNode(VariableNode("x"))),
        ("BACKWARD x", BackwardNode(VariableNode("x"))),
        ("LEFT x", LeftNode(VariableNode("x"))),
        ("RIGHT x", RightNode(VariableNode("x"))),
    ],
)
def test_movement_command_accepts_variable(source, expected):
    """Movement commands accept variable arguments."""
    assert parse_one(source) == expected


# ---------------------------------------------------------------------------
# Arithmetic arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source",
    [
        "FORWARD 10 + 20",
        "BACKWARD 10 + 20",
        "LEFT 10 + 20",
        "RIGHT 10 + 20",
    ],
)
def test_movement_command_accepts_arithmetic_expression(source):
    """Movement commands accept arithmetic expressions."""
    result = parse_one(source)

    expected = BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=LiteralNode(20),
    )

    assert (
        result.distance if isinstance(result, (ForwardNode, BackwardNode))
        else result.angle
    ) == expected


# ---------------------------------------------------------------------------
# Parenthesized arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source",
    [
        "FORWARD (10 + 20) * 2",
        "BACKWARD (10 + 20) * 2",
        "LEFT (10 + 20) * 2",
        "RIGHT (10 + 20) * 2",
    ],
)
def test_movement_command_accepts_parenthesized_expression(source):
    """Movement commands accept parenthesized arithmetic expressions."""
    result = parse_one(source)

    expected = BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
        op=TokenType.MULTIPLY,
        right=LiteralNode(2),
    )

    assert (
        result.distance if isinstance(result, (ForwardNode, BackwardNode))
        else result.angle
    ) == expected


# ---------------------------------------------------------------------------
# Missing arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source",
    [
        "FORWARD",
        "BACKWARD",
        "LEFT",
        "RIGHT",
    ],
)
def test_movement_command_requires_argument(source):
    """Every movement command requires an expression argument."""
    with pytest.raises(ParserError):
        parse(source)


# ---------------------------------------------------------------------------
# Invalid arguments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source",
    [
        "FORWARD [",
        "FORWARD )",
        "FORWARD IF",
        "BACKWARD [",
        "LEFT )",
        "RIGHT IF",
    ],
)
def test_movement_command_rejects_invalid_argument(source):
    """Movement commands reject tokens that cannot start an expression."""
    with pytest.raises(ParserError):
        parse(source)


# ===========================================================================
# PENUP / PENDOWN
# ===========================================================================


def test_penup():
    """PENUP creates a PenUpNode."""
    assert parse_one("PENUP") == PenUpNode()


def test_pendown():
    """PENDOWN creates a PenDownNode."""
    assert parse_one("PENDOWN") == PenDownNode()


def test_pen_commands_do_not_require_arguments():
    """PENUP and PENDOWN are complete statements without arguments."""
    result = parse(
        """
        PENUP
        PENDOWN
        """
    )

    assert result == [
        PenUpNode(),
        PenDownNode(),
    ]


# ===========================================================================
# COLOR
# ===========================================================================


def test_color_with_string():
    """COLOR accepts a string literal."""
    assert parse_one('COLOR "red"') == ColorNode(
        color_name=LiteralNode("red"),
    )


def test_color_with_parenthesized_expression():
    """
    COLOR uses parse_expression(), so a parenthesized expression is accepted
    syntactically.
    """
    assert parse_one("COLOR (x)") == ColorNode(
        color_name=VariableNode("x"),
    )


def test_color_requires_argument():
    """COLOR requires an expression argument."""
    with pytest.raises(ParserError):
        parse("COLOR")


# ===========================================================================
# WIDTH
# ===========================================================================


@pytest.mark.parametrize(
    "source,expected",
    [
        ("WIDTH 5", LiteralNode(5)),
        ("WIDTH x", VariableNode("x")),
        (
            "WIDTH 2 + 3",
            BinOpNode(
                left=LiteralNode(2),
                op=TokenType.PLUS,
                right=LiteralNode(3),
            ),
        ),
        (
            "WIDTH (2 + 3) * 2",
            BinOpNode(
                left=BinOpNode(
                    left=LiteralNode(2),
                    op=TokenType.PLUS,
                    right=LiteralNode(3),
                ),
                op=TokenType.MULTIPLY,
                right=LiteralNode(2),
            ),
        ),
    ],
)
def test_width_accepts_expression(source, expected):
    """WIDTH accepts literals, variables, and arithmetic expressions."""
    assert parse_one(source) == WidthNode(size=expected)


def test_width_requires_argument():
    """WIDTH requires an expression argument."""
    with pytest.raises(ParserError):
        parse("WIDTH")


# ===========================================================================
# SPEED
# ===========================================================================


@pytest.mark.parametrize(
    "source,expected",
    [
        ("SPEED 10", LiteralNode(10)),
        ("SPEED x", VariableNode("x")),
        (
            "SPEED 2 + 3",
            BinOpNode(
                left=LiteralNode(2),
                op=TokenType.PLUS,
                right=LiteralNode(3),
            ),
        ),
        (
            "SPEED (2 + 3) * 2",
            BinOpNode(
                left=BinOpNode(
                    left=LiteralNode(2),
                    op=TokenType.PLUS,
                    right=LiteralNode(3),
                ),
                op=TokenType.MULTIPLY,
                right=LiteralNode(2),
            ),
        ),
    ],
)
def test_speed_accepts_expression(source, expected):
    """SPEED accepts literals, variables, and arithmetic expressions."""
    assert parse_one(source) == SpeedNode(level=expected)


def test_speed_requires_argument():
    """SPEED requires an expression argument."""
    with pytest.raises(ParserError):
        parse("SPEED")


# ===========================================================================
# Command sequences
# ===========================================================================


def test_commands_preserve_source_order():
    """Commands are stored in the AST in their original source order."""
    result = parse(
        """
        PENUP
        FORWARD 100
        LEFT 90
        PENDOWN
        BACKWARD 50
        """
    )

    assert result == [
        PenUpNode(),
        ForwardNode(LiteralNode(100)),
        LeftNode(LiteralNode(90)),
        PenDownNode(),
        BackwardNode(LiteralNode(50)),
    ]
