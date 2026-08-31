import pytest

from Carapace.src.lexer import TokenType
from Carapace.src.ast import (
    LiteralNode, VariableNode, BinOpNode, FunctionCallNode, SetNode, ForwardNode,
)
from Carapace.src.errors import ParserError

from .conftest import parse, parse_one


# ===========================================================================
# Literals
# ===========================================================================


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------

def test_number_literal():
    """A number is parsed as a LiteralNode containing its numeric value."""
    result = parse_one("FORWARD 10")

    assert result.distance == LiteralNode(10)


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

def test_string_literal():
    """A string is parsed as a LiteralNode containing its string value."""
    result = parse_one('COLOR "red"')

    assert result.color_name == LiteralNode("red")


def test_empty_string_literal():
    """An empty string is a valid string literal."""
    result = parse_one('COLOR ""')

    assert result.color_name == LiteralNode("")


# ===========================================================================
# Variables
# ===========================================================================


# ---------------------------------------------------------------------------
# Valid variable names
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name",
    [
        "x",
        "size",
        "foo",
        "my_variable",
        "_",
        "___",
    ],
)
def test_variable_is_parsed_as_variable_node(name):
    """Valid identifiers are parsed as VariableNode objects."""
    result = parse_one(f"FORWARD {name}")

    assert result.distance == VariableNode(name)


def test_variable_preserves_original_case():
    """Variable names preserve their original spelling and casing."""
    result = parse_one("FORWARD myVar")

    assert result.distance == VariableNode("myVar")


# ===========================================================================
# Basic binary operations
# ===========================================================================


# ---------------------------------------------------------------------------
# Addition
# ---------------------------------------------------------------------------

def test_addition():
    """Addition creates a BinOpNode with PLUS as its operator."""
    result = parse_one("FORWARD 10 + 20")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=LiteralNode(20),
    )


# ---------------------------------------------------------------------------
# Subtraction
# ---------------------------------------------------------------------------

def test_subtraction():
    """Subtraction creates a BinOpNode with MINUS as its operator."""
    result = parse_one("FORWARD 10 - 20")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.MINUS,
        right=LiteralNode(20),
    )


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------

def test_multiplication():
    """Multiplication creates a BinOpNode with MULTIPLY as its operator."""
    result = parse_one("FORWARD 10 * 20")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.MULTIPLY,
        right=LiteralNode(20),
    )


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

def test_division():
    """Division creates a BinOpNode with DIVIDE as its operator."""
    result = parse_one("FORWARD 10 / 20")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.DIVIDE,
        right=LiteralNode(20),
    )


# ===========================================================================
# Operator associativity
# ===========================================================================


# ---------------------------------------------------------------------------
# Addition
# ---------------------------------------------------------------------------

def test_addition_is_left_associative():
    """Addition is left-associative: (10 + 20) + 30."""
    result = parse_one("FORWARD 10 + 20 + 30")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
        op=TokenType.PLUS,
        right=LiteralNode(30),
    )


# ---------------------------------------------------------------------------
# Subtraction
# ---------------------------------------------------------------------------

def test_subtraction_is_left_associative():
    """Subtraction is left-associative: (10 - 20) - 5."""
    result = parse_one("FORWARD 10 - 20 - 5")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.MINUS,
            right=LiteralNode(20),
        ),
        op=TokenType.MINUS,
        right=LiteralNode(5),
    )


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------

def test_multiplication_is_left_associative():
    """Multiplication is left-associative: (2 * 3) * 4."""
    result = parse_one("FORWARD 2 * 3 * 4")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(2),
            op=TokenType.MULTIPLY,
            right=LiteralNode(3),
        ),
        op=TokenType.MULTIPLY,
        right=LiteralNode(4),
    )


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

def test_division_is_left_associative():
    """Division is left-associative: (20 / 5) / 2."""
    result = parse_one("FORWARD 20 / 5 / 2")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(20),
            op=TokenType.DIVIDE,
            right=LiteralNode(5),
        ),
        op=TokenType.DIVIDE,
        right=LiteralNode(2),
    )


# ===========================================================================
# Operator precedence
# ===========================================================================


# ---------------------------------------------------------------------------
# Multiplication before addition
# ---------------------------------------------------------------------------

def test_multiplication_has_higher_precedence_than_addition():
    """Multiplication binds more strongly than addition."""
    result = parse_one("FORWARD 10 + 20 * 3")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=BinOpNode(
            left=LiteralNode(20),
            op=TokenType.MULTIPLY,
            right=LiteralNode(3),
        ),
    )


# ---------------------------------------------------------------------------
# Division before subtraction
# ---------------------------------------------------------------------------

def test_division_has_higher_precedence_than_subtraction():
    """Division binds more strongly than subtraction."""
    result = parse_one("FORWARD 10 - 20 / 5")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.MINUS,
        right=BinOpNode(
            left=LiteralNode(20),
            op=TokenType.DIVIDE,
            right=LiteralNode(5),
        ),
    )


# ---------------------------------------------------------------------------
# Mixed expression
# ---------------------------------------------------------------------------

def test_mixed_expression_preserves_complete_ast():
    """A mixed expression preserves both precedence and associativity."""
    result = parse_one("FORWARD 10 + 20 * 3 - 5 / 2")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=BinOpNode(
                left=LiteralNode(20),
                op=TokenType.MULTIPLY,
                right=LiteralNode(3),
            ),
        ),
        op=TokenType.MINUS,
        right=BinOpNode(
            left=LiteralNode(5),
            op=TokenType.DIVIDE,
            right=LiteralNode(2),
        ),
    )


# ===========================================================================
# Parentheses
# ===========================================================================


def test_parenthesized_literal():
    """Parentheses around a single expression are accepted."""
    result = parse_one("FORWARD (10)")

    assert result.distance == LiteralNode(10)


def test_parenthesized_addition():
    """Parentheses can explicitly group an addition expression."""
    result = parse_one("FORWARD (10 + 20)")

    assert result.distance == BinOpNode(
        left=LiteralNode(10),
        op=TokenType.PLUS,
        right=LiteralNode(20),
    )


def test_parentheses_change_precedence():
    """Parentheses make addition bind before multiplication."""
    result = parse_one("FORWARD (10 + 20) * 3")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
        op=TokenType.MULTIPLY,
        right=LiteralNode(3),
    )


def test_nested_parentheses():
    """Nested parentheses are parsed recursively."""
    result = parse_one("FORWARD ((10 + 20) * 3)")

    assert result.distance == BinOpNode(
        left=BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
        op=TokenType.MULTIPLY,
        right=LiteralNode(3),
    )


def test_deeply_nested_parentheses():
    """Multiple redundant levels of parentheses are accepted."""
    result = parse_one("FORWARD (((10)))")

    assert result.distance == LiteralNode(10)


# ===========================================================================
# Invalid parentheses
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "FORWARD (10",
        "FORWARD 10)",
        "FORWARD ()",
        "FORWARD (10 +)",
        "FORWARD (+ 10)",
        "FORWARD (10 * )",
    ],
)
def test_invalid_parentheses_raise_parser_error(source):
    """Unbalanced and empty parentheses are rejected by the parser."""
    with pytest.raises(ParserError):
        parse(source)


# ===========================================================================
# Invalid expressions
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "FORWARD +",
        "FORWARD -",
        "FORWARD *",
        "FORWARD /",
        "FORWARD 10 +",
        "FORWARD 10 -",
        "FORWARD 10 *",
        "FORWARD 10 /",
        "FORWARD 10 + * 20",
        "FORWARD 10 * / 20",
        "FORWARD 10 / + 20",
    ],
)
def test_invalid_expression_raises_parser_error(source):
    """The parser rejects syntactically invalid arithmetic expressions."""
    with pytest.raises(ParserError):
        parse(source)


# ===========================================================================
# Function calls as expressions
# ===========================================================================


# ---------------------------------------------------------------------------
# CALL as a factor
# ---------------------------------------------------------------------------

def test_function_call_can_be_used_as_expression():
    """CALL is accepted as a factor inside an expression."""
    result = parse_one("SET x CALL foo")

    assert result == SetNode(
        name="x",
        value=FunctionCallNode(
            name="foo",
            args=[],
        ),
    )


def test_function_call_can_be_left_operand_of_expression():
    """A function call can be the left operand of an arithmetic expression."""
    result = parse_one("SET x CALL foo + 10")

    assert result == SetNode(
        name="x",
        value=BinOpNode(
            left=FunctionCallNode(
                name="foo",
                args=[],
            ),
            op=TokenType.PLUS,
            right=LiteralNode(10),
        ),
    )


# ===========================================================================
# Function call arguments
# ===========================================================================


def test_function_call_without_arguments():
    """CALL can be used without arguments."""
    result = parse_one("CALL foo")

    assert result == FunctionCallNode(
        name="foo",
        args=[],
    )


def test_function_call_with_number_argument():
    """A numeric literal can be passed as a function argument."""
    result = parse_one("CALL foo 10")

    assert result.args == [
        LiteralNode(10),
    ]


def test_function_call_with_variable_argument():
    """A variable can be passed as a function argument."""
    result = parse_one("CALL foo x")

    assert result.args == [
        VariableNode("x"),
    ]


def test_function_call_with_string_argument():
    """A string can be passed as a function argument."""
    result = parse_one('CALL foo "red"')

    assert result.args == [
        LiteralNode("red"),
    ]


def test_function_call_with_multiple_arguments():
    """CALL can contain multiple arguments."""
    result = parse_one("CALL foo 10 20")

    assert result.args == [
        LiteralNode(10),
        LiteralNode(20),
    ]


def test_function_call_with_mixed_arguments():
    """CALL can combine literals and variables as arguments."""
    result = parse_one('CALL foo 10 x "red"')

    assert result.args == [
        LiteralNode(10),
        VariableNode("x"),
        LiteralNode("red"),
    ]


# ===========================================================================
# CALL argument boundaries
# ===========================================================================


def test_call_expression_is_one_argument():
    """An arithmetic expression after CALL is parsed as one argument."""
    result = parse_one("CALL foo 10 + 20")

    assert result.args == [
        BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
    ]


def test_call_can_have_multiple_expression_arguments():
    """
    Each expression is parsed independently when another expression-starting
    token follows the previous expression.
    """
    result = parse_one("CALL foo 10 + 20 x * 2")

    assert result.args == [
        BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
        BinOpNode(
            left=VariableNode("x"),
            op=TokenType.MULTIPLY,
            right=LiteralNode(2),
        ),
    ]


def test_call_parenthesized_argument():
    """A parenthesized expression is parsed as one CALL argument."""
    result = parse_one("CALL foo (10 + 20)")

    assert result.args == [
        BinOpNode(
            left=LiteralNode(10),
            op=TokenType.PLUS,
            right=LiteralNode(20),
        ),
    ]


# ===========================================================================
# CALL errors
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "CALL",
        "CALL 10",
        "CALL [",
        "CALL foo +",
    ],
)
def test_invalid_function_call_raises_parser_error(source):
    """CALL requires a function name and valid arguments."""
    with pytest.raises(ParserError):
        parse(source)
