import pytest

from Carapace.src.errors import SemanticError
from Carapace.tests.conftest import analyze


# ===========================================================================
# Function lookup and arity
# ===========================================================================


def test_defined_function_call_is_valid():
    """Calling a declared global function is semantically valid."""
    analyze("""
        FUNC draw [
            FORWARD 10
        ]

        CALL draw
    """)


def test_undefined_function_is_rejected():
    """Undefined function names are known statically after declaration collection."""
    with pytest.raises(SemanticError, match="missing"):
        analyze("CALL missing")


def test_function_call_with_correct_arity_is_valid():
    """A call with exactly one argument per parameter is accepted."""
    analyze("""
        FUNC move distance angle [
            FORWARD distance
            RIGHT angle
        ]

        CALL move 100 90
    """)


def test_function_call_with_too_few_arguments_is_rejected():
    """Too few arguments produce SemanticError."""
    with pytest.raises(SemanticError, match="move"):
        analyze("""
            FUNC move distance angle [
                FORWARD distance
            ]

            CALL move 100
        """)


def test_function_call_with_too_many_arguments_is_rejected():
    """Too many arguments produce SemanticError."""
    with pytest.raises(SemanticError, match="move"):
        analyze("""
            FUNC move distance [
                FORWARD distance
            ]

            CALL move 100 90
        """)


# ===========================================================================
# RETURN context
# ===========================================================================


def test_return_inside_function_is_valid():
    """RETURN is valid inside a function body."""
    analyze("""
        FUNC answer [
            RETURN 42
        ]
    """)


def test_return_inside_if_inside_function_is_valid():
    """Function context propagates through IF blocks."""
    analyze("""
        FUNC answer x [
            IF x > 0 [
                RETURN x
            ]
        ]
    """)


def test_return_inside_repeat_inside_function_is_valid():
    """Function context propagates through REPEAT blocks."""
    analyze("""
        FUNC answer [
            REPEAT 1 [
                RETURN 42
            ]
        ]
    """)


def test_return_at_top_level_is_rejected():
    """RETURN outside a function is a semantic error."""
    with pytest.raises(SemanticError):
        analyze("RETURN 42")


# ===========================================================================
# Value-producing calls
# ===========================================================================


def test_procedure_call_as_statement_is_valid():
    """A standalone CALL does not require the function to return a value."""
    analyze("""
        FUNC draw [
            FORWARD 10
        ]

        CALL draw
    """)


def test_returning_function_call_as_statement_is_valid():
    """A returned value is allowed to be discarded in statement context."""
    analyze("""
        FUNC answer [
            RETURN 42
        ]

        CALL answer
    """)


def test_function_without_return_cannot_be_used_as_expression():
    """A function with no RETURN anywhere cannot satisfy expression context."""
    with pytest.raises(SemanticError, match="draw"):
        analyze("""
            FUNC draw [
                FORWARD 10
            ]

            SET result CALL draw
        """)


def test_conditional_return_allows_expression_call_semantically():
    """The analyzer does not attempt to prove that every execution path returns."""
    analyze("""
        FUNC maybe x [
            IF x > 0 [
                RETURN x
            ]
        ]

        SET result CALL maybe 10
    """)


def test_nested_return_counts_as_function_return_capability():
    """A RETURN nested inside control flow is discovered structurally."""
    _, result = analyze("""
        FUNC maybe x [
            REPEAT 1 [
                IF x > 0 [
                    RETURN x
                ]
            ]
        ]
    """)

    assert result.functions["maybe"].has_return_statement is True


def test_function_without_return_is_marked_as_non_returning():
    """Function metadata records absence of any RETURN statement."""
    _, result = analyze("""
        FUNC draw [
            FORWARD 10
        ]
    """)

    assert result.functions["draw"].has_return_statement is False
