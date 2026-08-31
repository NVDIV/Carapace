import pytest

from Carapace.src.errors import ParserError

from Carapace.src.ast import (
    SetNode, LiteralNode, VariableNode, BinOpNode, ForwardNode, RightNode, PenUpNode, PenDownNode, ColorNode, WidthNode, RepeatNode, IfNode, FunctionDefNode, FunctionCallNode, ReturnNode,
)

from Carapace.tests.conftest import parse


# ===========================================================================
# Basic programs
# ===========================================================================


# ---------------------------------------------------------------------------
# Empty program
# ---------------------------------------------------------------------------

def test_empty_program():
    """An empty source program produces an empty AST."""
    assert parse("") == []


# ---------------------------------------------------------------------------
# Multiple top-level statements
# ---------------------------------------------------------------------------

def test_program_preserves_statement_order():
    """Top-level statements remain in exactly the source order."""
    result = parse(
        """
        SET a 1
        SET b 2
        SET c 3
        """
    )

    assert result == [
        SetNode("a", LiteralNode(1)),
        SetNode("b", LiteralNode(2)),
        SetNode("c", LiteralNode(3)),
    ]


# ===========================================================================
# Realistic turtle programs
# ===========================================================================


def test_simple_turtle_program():
    """A simple turtle program produces the expected complete AST."""
    result = parse(
        """
        SET size 100

        PENUP
        FORWARD 50
        PENDOWN

        REPEAT 4 [
            FORWARD size
            RIGHT 90
        ]
        """
    )

    assert result == [
        SetNode(
            name="size",
            value=LiteralNode(100),
        ),
        PenUpNode(),
        ForwardNode(
            distance=LiteralNode(50),
        ),
        PenDownNode(),
        RepeatNode(
            times=LiteralNode(4),
            body=[
                ForwardNode(
                    distance=VariableNode("size"),
                ),
                RightNode(
                    angle=LiteralNode(90),
                ),
            ],
        ),
    ]


def test_program_with_if_and_commands():
    """A program containing IF and several commands preserves its full AST."""
    result = parse(
        """
        SET x 10

        IF x > 5 [
            COLOR "red"
            WIDTH 3
            FORWARD x * 2
        ]
        """
    )

    assert result == [
        SetNode(
            name="x",
            value=LiteralNode(10),
        ),
        IfNode(
            left=VariableNode("x"),
            op=__import__("src.lexer", fromlist=["TokenType"]).TokenType.GT,
            right=LiteralNode(5),
            body=[
                ColorNode(
                    color_name=LiteralNode("red"),
                ),
                WidthNode(
                    size=LiteralNode(3),
                ),
                ForwardNode(
                    distance=BinOpNode(
                        left=VariableNode("x"),
                        op=__import__(
                            "src.lexer",
                            fromlist=["TokenType"],
                        ).TokenType.MULTIPLY,
                        right=LiteralNode(2),
                    ),
                ),
            ],
        ),
    ]


# ===========================================================================
# Functions
# ===========================================================================


def test_function_definition_and_call():
    """A function definition followed by CALL creates two top-level nodes."""
    result = parse(
        """
        FUNC square size [
            REPEAT 4 [
                FORWARD size
                RIGHT 90
            ]
        ]

        CALL square 100
        """
    )

    assert len(result) == 2

    assert result[0] == FunctionDefNode(
        name="square",
        params=["size"],
        body=[
            RepeatNode(
                times=LiteralNode(4),
                body=[
                    ForwardNode(VariableNode("size")),
                    RightNode(LiteralNode(90)),
                ],
            ),
        ],
    )

    assert result[1] == FunctionCallNode(
        name="square",
        args=[
            LiteralNode(100),
        ],
    )


def test_function_program_with_variable_argument():
    """A function can be called with a variable as its argument."""
    result = parse(
        """
        FUNC square size [
            REPEAT 4 [
                FORWARD size
                RIGHT 90
            ]
        ]

        SET size 100
        CALL square size
        """
    )

    assert result == [
        FunctionDefNode(
            name="square",
            params=["size"],
            body=[
                RepeatNode(
                    times=LiteralNode(4),
                    body=[
                        ForwardNode(VariableNode("size")),
                        RightNode(LiteralNode(90)),
                    ],
                ),
            ],
        ),
        SetNode(
            name="size",
            value=LiteralNode(100),
        ),
        FunctionCallNode(
            name="square",
            args=[
                VariableNode("size"),
            ],
        ),
    ]


# ===========================================================================
# Complex function program
# ===========================================================================


def test_function_with_assignment_and_return():
    """A function can contain SET and RETURN statements."""
    result = parse(
        """
        FUNC double x [
            SET result x * 2
            RETURN result
        ]
        """
    )

    assert result == [
        FunctionDefNode(
            name="double",
            params=["x"],
            body=[
                SetNode(
                    name="result",
                    value=BinOpNode(
                        left=VariableNode("x"),
                        op=__import__(
                            "src.lexer",
                            fromlist=["TokenType"],
                        ).TokenType.MULTIPLY,
                        right=LiteralNode(2),
                    ),
                ),
                ReturnNode(
                    value=VariableNode("result"),
                ),
            ],
        ),
    ]


# ===========================================================================
# Nested control flow
# ===========================================================================


def test_complex_nested_program():
    """Nested IF and REPEAT constructs produce the expected AST hierarchy."""
    result = parse(
        """
        SET x 10

        REPEAT 4 [
            IF x > 5 [
                FORWARD x
                RIGHT 90
            ]
        ]
        """
    )

    assert result == [
        SetNode(
            name="x",
            value=LiteralNode(10),
        ),
        RepeatNode(
            times=LiteralNode(4),
            body=[
                IfNode(
                    left=VariableNode("x"),
                    op=__import__(
                        "src.lexer",
                        fromlist=["TokenType"],
                    ).TokenType.GT,
                    right=LiteralNode(5),
                    body=[
                        ForwardNode(VariableNode("x")),
                        RightNode(LiteralNode(90)),
                    ],
                ),
            ],
        ),
    ]


# ===========================================================================
# Parser side effects
# ===========================================================================


def test_parser_only_builds_ast():
    """
    Parsing a turtle command creates an AST node and does not execute it.

    Parser tests therefore do not require a turtle window or graphical state.
    """
    result = parse("FORWARD 100")

    assert result == [
        ForwardNode(LiteralNode(100)),
    ]

# ===========================================================================
# Function syntax errors
# ===========================================================================


def test_unclosed_function_block_raises_parser_error():
    """EOF inside a FUNC body is reported as a parser error, not an internal error."""
    import pytest

    from Carapace.src.errors import ParserError

    with pytest.raises(ParserError, match="Unclosed FUNC block"):
        parse("""
            FUNC draw size [
                FORWARD size
        """)


def test_unclosed_function_error_contains_opening_line():
    """An unclosed FUNC reports the source line where the declaration started."""
    with pytest.raises(ParserError, match=r"Line 2: Unclosed FUNC"):
        parse("""
FUNC draw [
    FORWARD 10
""")
