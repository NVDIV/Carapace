import pytest

from Carapace.src.errors import RuntimeError as CarapaceRuntimeError
from Carapace.tests.conftest import analyze


def make_interpreter(source):
    """Create an interpreter from semantically valid source."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    return Interpreter(tree, semantic_result)


# ===========================================================================
# Arithmetic runtime errors
# ===========================================================================


def test_division_by_zero_is_carapace_runtime_error(command_mocks):
    """Division by zero never leaks Python ZeroDivisionError."""
    interpreter = make_interpreter("SET x 10 / 0")

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


def test_unknown_parameter_resolving_to_wrong_arithmetic_type_is_runtime_error(
    command_mocks,
):
    """UNKNOWN static types are validated against concrete runtime values."""
    interpreter = make_interpreter("""
        FUNC add_ten x [
            RETURN x + 10
        ]

        SET result CALL add_ten "hello"
    """)

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


# ===========================================================================
# Command runtime errors
# ===========================================================================


def test_unknown_parameter_resolving_to_wrong_command_type_is_runtime_error(
    command_mocks,
):
    """A parameter passed to a numeric command is checked at runtime."""
    interpreter = make_interpreter("""
        FUNC move distance [
            FORWARD distance
        ]

        CALL move "hello"
    """)

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


def test_unknown_parameter_resolving_to_wrong_color_type_is_runtime_error(
    command_mocks,
):
    """COLOR validates an UNKNOWN value once the runtime value is known."""
    interpreter = make_interpreter("""
        FUNC paint paint_value [
            COLOR paint_value
        ]

        CALL paint 10
    """)

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


def test_speed_above_supported_range_is_runtime_error(command_mocks):
    """SPEED validates the turtle-compatible 0..10 value range."""
    interpreter = make_interpreter("SPEED 11")

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


def test_width_zero_is_runtime_error(command_mocks):
    """WIDTH rejects non-positive runtime values."""
    interpreter = make_interpreter("WIDTH 0")

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()


# ===========================================================================
# Control-flow-dependent runtime errors
# ===========================================================================


def test_variable_declared_in_unexecuted_if_is_runtime_error(command_mocks):
    """A semantic symbol may still lack a runtime value on the executed path."""
    interpreter = make_interpreter("""
        IF 1 == 0 [
            SET x 10
        ]

        FORWARD x
    """)

    with pytest.raises(CarapaceRuntimeError, match="x"):
        interpreter.run()


def test_variable_declared_in_zero_repeat_is_runtime_error(command_mocks):
    """REPEAT does not guarantee that a semantically known assignment executes."""
    interpreter = make_interpreter("""
        REPEAT 0 [
            SET x 10
        ]

        FORWARD x
    """)

    with pytest.raises(CarapaceRuntimeError, match="x"):
        interpreter.run()


def test_conditional_return_fallthrough_is_runtime_error(command_mocks):
    """Expression calls require an actual value on the concrete execution path."""
    interpreter = make_interpreter("""
        FUNC maybe x [
            IF x > 0 [
                RETURN x
            ]
        ]

        SET result CALL maybe 0
    """)

    with pytest.raises(CarapaceRuntimeError, match="maybe"):
        interpreter.run()


# ===========================================================================
# Backend error translation
# ===========================================================================


def test_invalid_backend_color_is_translated_to_runtime_error(
    command_mocks,
):
    """A user-caused turtle color failure is exposed as Carapace RuntimeError."""
    command_mocks.execute_color.side_effect = ValueError("invalid color")

    interpreter = make_interpreter('COLOR "not-a-color"')

    with pytest.raises(CarapaceRuntimeError):
        interpreter.run()
