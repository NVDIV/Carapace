import pytest

from Carapace.src.lexer import TokenType
from Carapace.src.ast import (
    LiteralNode, VariableNode, BinOpNode, ForwardNode, RightNode, RepeatNode, IfNode,
)
from Carapace.src.errors import ParserError

from Carapace.tests.conftest import parse, parse_one


# ===========================================================================
# REPEAT
# ===========================================================================


# ---------------------------------------------------------------------------
# Repeat count
# ---------------------------------------------------------------------------

def test_repeat_with_literal_count():
    """REPEAT accepts a numeric literal as its iteration count."""
    result = parse_one("REPEAT 4 []")

    assert result == RepeatNode(
        times=LiteralNode(4),
        body=[],
    )


def test_repeat_with_variable_count():
    """REPEAT accepts a variable as its iteration count."""
    result = parse_one("REPEAT n []")

    assert result == RepeatNode(
        times=VariableNode("n"),
        body=[],
    )


def test_repeat_with_expression_count():
    """REPEAT accepts an arithmetic expression as its count."""
    result = parse_one("REPEAT 2 + 2 []")

    assert result == RepeatNode(
        times=BinOpNode(
            left=LiteralNode(2),
            op=TokenType.PLUS,
            right=LiteralNode(2),
        ),
        body=[],
    )


def test_repeat_with_parenthesized_count():
    """REPEAT accepts a parenthesized expression as its count."""
    result = parse_one("REPEAT (2 + 2) []")

    assert result == RepeatNode(
        times=BinOpNode(
            left=LiteralNode(2),
            op=TokenType.PLUS,
            right=LiteralNode(2),
        ),
        body=[],
    )


# ===========================================================================
# REPEAT body
# ===========================================================================


def test_repeat_with_empty_body():
    """A REPEAT block may contain no statements."""
    result = parse_one("REPEAT 4 []")

    assert result.body == []


def test_repeat_with_one_statement():
    """A REPEAT block can contain one statement."""
    result = parse_one(
        """
        REPEAT 4 [
            FORWARD 100
        ]
        """
    )

    assert result.body == [
        ForwardNode(LiteralNode(100)),
    ]


def test_repeat_with_multiple_statements():
    """A REPEAT block preserves the order of multiple statements."""
    result = parse_one(
        """
        REPEAT 4 [
            FORWARD 100
            RIGHT 90
        ]
        """
    )

    assert result.body == [
        ForwardNode(LiteralNode(100)),
        RightNode(LiteralNode(90)),
    ]


# ---------------------------------------------------------------------------
# Nested REPEAT
# ---------------------------------------------------------------------------

def test_nested_repeat():
    """REPEAT blocks can contain other REPEAT blocks."""
    result = parse_one(
        """
        REPEAT 4 [
            REPEAT 2 [
                FORWARD 10
            ]
        ]
        """
    )

    assert result == RepeatNode(
        times=LiteralNode(4),
        body=[
            RepeatNode(
                times=LiteralNode(2),
                body=[
                    ForwardNode(LiteralNode(10)),
                ],
            ),
        ],
    )


# ===========================================================================
# IF
# ===========================================================================


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "operator,token_type",
    [
        ("==", TokenType.EQ),
        ("<", TokenType.LT),
        (">", TokenType.GT),
    ],
)
def test_if_accepts_comparison_operator(operator, token_type):
    """IF accepts all comparison operators supported by the grammar."""
    result = parse_one(f"IF x {operator} 10 []")

    assert result == IfNode(
        left=VariableNode("x"),
        op=token_type,
        right=LiteralNode(10),
        body=[],
    )


# ---------------------------------------------------------------------------
# IF expressions
# ---------------------------------------------------------------------------

def test_if_with_expression_on_left():
    """The left side of an IF comparison can be an expression."""
    result = parse_one("IF x + 1 > 10 []")

    assert result.left == BinOpNode(
        left=VariableNode("x"),
        op=TokenType.PLUS,
        right=LiteralNode(1),
    )


def test_if_with_expression_on_right():
    """The right side of an IF comparison can be an expression."""
    result = parse_one("IF x > 10 + 5 []")

    assert result.right == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=LiteralNode(5),
    )


def test_if_with_expressions_on_both_sides():
    """Both sides of an IF comparison can be arithmetic expressions."""
    result = parse_one("IF x + 1 > y * 2 []")

    assert result.left == BinOpNode(
        left=VariableNode("x"),
        op=TokenType.PLUS,
        right=LiteralNode(1),
    )

    assert result.right == BinOpNode(
        left=VariableNode("y"),
        op=TokenType.MULTIPLY,
        right=LiteralNode(2),
    )


def test_if_with_parenthesized_expressions():
    """Parentheses are accepted on both sides of an IF comparison."""
    result = parse_one("IF (x + 1) > (y * 2) []")

    assert result.left == BinOpNode(
        left=VariableNode("x"),
        op=TokenType.PLUS,
        right=LiteralNode(1),
    )

    assert result.right == BinOpNode(
        left=VariableNode("y"),
        op=TokenType.MULTIPLY,
        right=LiteralNode(2),
    )


# ===========================================================================
# IF body
# ===========================================================================


def test_if_with_empty_body():
    """An IF block may contain no statements."""
    result = parse_one("IF x > 10 []")

    assert result.body == []


def test_if_with_one_statement():
    """An IF block can contain one statement."""
    result = parse_one(
        """
        IF x > 10 [
            FORWARD 100
        ]
        """
    )

    assert result.body == [
        ForwardNode(LiteralNode(100)),
    ]


def test_if_with_multiple_statements():
    """An IF block preserves the order of multiple statements."""
    result = parse_one(
        """
        IF x > 10 [
            FORWARD 100
            RIGHT 90
        ]
        """
    )

    assert result.body == [
        ForwardNode(LiteralNode(100)),
        RightNode(LiteralNode(90)),
    ]


# ---------------------------------------------------------------------------
# Nested IF
# ---------------------------------------------------------------------------

def test_nested_if():
    """IF blocks can contain other IF statements."""
    result = parse_one(
        """
        IF x > 10 [
            IF y < 5 [
                FORWARD 100
            ]
        ]
        """
    )

    assert result == IfNode(
        left=VariableNode("x"),
        op=TokenType.GT,
        right=LiteralNode(10),
        body=[
            IfNode(
                left=VariableNode("y"),
                op=TokenType.LT,
                right=LiteralNode(5),
                body=[
                    ForwardNode(LiteralNode(100)),
                ],
            ),
        ],
    )


# ===========================================================================
# Nested control-flow constructs
# ===========================================================================


def test_if_inside_repeat():
    """An IF statement can appear inside a REPEAT block."""
    result = parse_one(
        """
        REPEAT 4 [
            IF x > 10 [
                FORWARD 100
            ]
        ]
        """
    )

    assert result == RepeatNode(
        times=LiteralNode(4),
        body=[
            IfNode(
                left=VariableNode("x"),
                op=TokenType.GT,
                right=LiteralNode(10),
                body=[
                    ForwardNode(LiteralNode(100)),
                ],
            ),
        ],
    )


def test_repeat_inside_if():
    """A REPEAT statement can appear inside an IF block."""
    result = parse_one(
        """
        IF x > 10 [
            REPEAT 4 [
                FORWARD 100
            ]
        ]
        """
    )

    assert result == IfNode(
        left=VariableNode("x"),
        op=TokenType.GT,
        right=LiteralNode(10),
        body=[
            RepeatNode(
                times=LiteralNode(4),
                body=[
                    ForwardNode(LiteralNode(100)),
                ],
            ),
        ],
    )


# ===========================================================================
# REPEAT errors
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "REPEAT []",
        "REPEAT 4",
        "REPEAT 4 (",
    ],
)
def test_repeat_rejects_invalid_header(source):
    """REPEAT requires a count expression followed by an opening bracket."""
    with pytest.raises(ParserError):
        parse(source)


def test_repeat_rejects_unclosed_block():
    """An unclosed REPEAT block raises ParserError instead of IndexError."""
    with pytest.raises(ParserError):
        parse(
            """
            REPEAT 4 [
                FORWARD 100
            """
        )


def test_nested_repeat_rejects_unclosed_inner_block():
    """An unclosed nested REPEAT block raises ParserError."""
    with pytest.raises(ParserError):
        parse(
            """
            REPEAT 4 [
                REPEAT 2 [
                    FORWARD 10
                ]
            """
        )


# ===========================================================================
# IF errors
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "IF []",
        "IF x 10 []",
        "IF x + 10 []",
        "IF x > []",
        "IF x > 10",
    ],
)
def test_if_rejects_invalid_syntax(source):
    """IF requires two expressions, a comparison operator, and a body."""
    with pytest.raises(ParserError):
        parse(source)


def test_if_rejects_unclosed_block():
    """An unclosed IF block raises ParserError."""
    with pytest.raises(ParserError):
        parse(
            """
            IF x > 10 [
                FORWARD 100
            """
        )

def test_unclosed_repeat_error_contains_opening_line():
    """An unclosed REPEAT reports the source line where the block started."""
    with pytest.raises(ParserError, match=r"Line 2: Unclosed REPEAT"):
        parse("""
REPEAT 2 [
    FORWARD 10
""")


def test_unclosed_if_error_contains_opening_line():
    """An unclosed IF reports the source line where the block started."""
    with pytest.raises(ParserError, match=r"Line 2: Unclosed IF"):
        parse("""
IF 1 == 1 [
    FORWARD 10
""")
