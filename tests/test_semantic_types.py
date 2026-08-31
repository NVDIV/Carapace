import pytest

from Carapace.src.errors import SemanticError
from Carapace.tests.conftest import analyze


# ===========================================================================
# Arithmetic
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "SET x 10 + 20",
        "SET x 10 - 20",
        "SET x 10 * 20",
        "SET x 10 / 20",
    ],
)
def test_numeric_arithmetic_is_valid(source):
    """Arithmetic operators accept statically known numeric operands."""
    analyze(source)


@pytest.mark.parametrize(
    "source",
    [
        'SET x "a" + "b"',
        'SET x "a" - "b"',
        'SET x "a" * "b"',
        'SET x "a" / "b"',
        'SET x 10 + "b"',
    ],
)
def test_known_invalid_arithmetic_types_are_rejected(source):
    """Statically provable arithmetic type mismatches are SemanticError."""
    with pytest.raises(SemanticError):
        analyze(source)


def test_unknown_parameter_type_is_deferred_to_runtime():
    """An UNKNOWN parameter is not rejected merely because runtime validation is needed."""
    analyze("""
        FUNC add_ten x [
            RETURN x + 10
        ]
    """)


def test_function_call_result_type_is_unknown():
    """No static return-type inference is required for a function-call expression."""
    analyze("""
        FUNC value [
            RETURN 10
        ]

        SET result (CALL value) + 5
    """)


# ===========================================================================
# Command argument types
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "FORWARD 10",
        "BACKWARD 10",
        "LEFT 90",
        "RIGHT 90",
        "WIDTH 3",
        "SPEED 5",
        "REPEAT 2 [ FORWARD 10 ]",
    ],
)
def test_numeric_construct_accepts_known_number(source):
    """Numeric commands and REPEAT accept statically known numbers."""
    analyze(source)


@pytest.mark.parametrize(
    "source",
    [
        'FORWARD "red"',
        'BACKWARD "red"',
        'LEFT "red"',
        'RIGHT "red"',
        'WIDTH "wide"',
        'SPEED "fast"',
        'REPEAT "two" [ FORWARD 10 ]',
    ],
)
def test_numeric_construct_rejects_known_string(source):
    """Known STRING values are rejected where NUMBER is required."""
    with pytest.raises(SemanticError):
        analyze(source)


def test_color_accepts_known_string():
    """COLOR requires a string expression."""
    analyze('COLOR "red"')


def test_color_rejects_known_number():
    """A statically known number cannot be used as a color."""
    with pytest.raises(SemanticError):
        analyze("COLOR 10")


def test_unknown_command_argument_is_deferred_to_runtime():
    """UNKNOWN parameter types are checked only when concrete runtime values exist."""
    analyze("""
        FUNC draw distance paint [
            FORWARD distance
            COLOR paint
        ]
    """)


# ===========================================================================
# Comparisons
# ===========================================================================


@pytest.mark.parametrize(
    "source",
    [
        "IF 10 == 20 [ FORWARD 1 ]",
        "IF 10 < 20 [ FORWARD 1 ]",
        "IF 10 > 20 [ FORWARD 1 ]",
        'IF "a" == "b" [ FORWARD 1 ]',
    ],
)
def test_valid_known_comparisons_are_accepted(source):
    """Numeric ordering and same-type scalar equality are valid."""
    analyze(source)


@pytest.mark.parametrize(
    "source",
    [
        'IF "a" < "b" [ FORWARD 1 ]',
        'IF "a" > "b" [ FORWARD 1 ]',
        'IF 10 == "10" [ FORWARD 1 ]',
    ],
)
def test_invalid_known_comparisons_are_rejected(source):
    """Statically incompatible comparisons are SemanticError."""
    with pytest.raises(SemanticError):
        analyze(source)


def test_unknown_comparison_operand_is_deferred_to_runtime():
    """A comparison involving an UNKNOWN parameter is not rejected statically."""
    analyze("""
        FUNC positive x [
            IF x > 0 [
                RETURN x
            ]
        ]
    """)
