import pytest

from Carapace.tests.conftest import analyze


def make_interpreter(source):
    """Create an interpreter from semantically valid source."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    return Interpreter(tree, semantic_result)


# ===========================================================================
# Turtle command dispatch
# ===========================================================================


@pytest.mark.parametrize(
    "source,mock_name,value",
    [
        ("FORWARD 100", "execute_forward", 100),
        ("BACKWARD 50", "execute_backward", 50),
        ("LEFT 90", "execute_left", 90),
        ("RIGHT 45", "execute_right", 45),
        ('COLOR "red"', "execute_color", "red"),
        ("WIDTH 3", "execute_width", 3),
        ("SPEED 5", "execute_speed", 5),
    ],
)
def test_value_command_dispatches_evaluated_argument(
    source,
    mock_name,
    value,
    command_mocks,
):
    """Value-taking commands receive the evaluated Carapace expression value."""
    interpreter = make_interpreter(source)

    interpreter.run()

    getattr(command_mocks, mock_name).assert_called_once_with(value)


def test_penup_dispatches_without_argument(command_mocks):
    """PENUP delegates to the command adapter exactly once."""
    interpreter = make_interpreter("PENUP")

    interpreter.run()

    command_mocks.execute_penup.assert_called_once_with()


def test_pendown_dispatches_without_argument(command_mocks):
    """PENDOWN delegates to the command adapter exactly once."""
    interpreter = make_interpreter("PENDOWN")

    interpreter.run()

    command_mocks.execute_pendown.assert_called_once_with()


def test_command_argument_expression_is_evaluated_before_dispatch(command_mocks):
    """The command adapter receives values rather than AST expression nodes."""
    interpreter = make_interpreter("""
        SET x 10
        FORWARD x * 2
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(20)
