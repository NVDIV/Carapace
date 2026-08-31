import pytest

from Carapace.src.errors import SemanticError, RuntimeError as CarapaceRuntimeError
from Carapace.tests.conftest import analyze


def execute(source, command_mocks):
    """Execute the complete validated Carapace pipeline."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    interpreter = Interpreter(tree, semantic_result)
    interpreter.run()
    return interpreter


# ===========================================================================
# Complete programs
# ===========================================================================


def test_complete_square_program(command_mocks):
    """Variables, REPEAT and turtle commands work together end-to-end."""
    execute("""
        SET size 100

        REPEAT 4 [
            FORWARD size
            RIGHT 90
        ]
    """, command_mocks)

    assert [call.args[0] for call in command_mocks.execute_forward.call_args_list] == [
        100, 100, 100, 100
    ]
    assert [call.args[0] for call in command_mocks.execute_right.call_args_list] == [
        90, 90, 90, 90
    ]


def test_complete_function_program(command_mocks):
    """Function parameters and loops work through the complete pipeline."""
    execute("""
        FUNC square size [
            REPEAT 4 [
                FORWARD size
                RIGHT 90
            ]
        ]

        CALL square 50
    """, command_mocks)

    assert command_mocks.execute_forward.call_count == 4
    command_mocks.execute_forward.assert_any_call(50)


def test_complete_forward_declaration_program(command_mocks):
    """A function can execute before its textual FUNC statement."""
    execute("""
        CALL square 25

        FUNC square size [
            REPEAT 4 [
                FORWARD size
                RIGHT 90
            ]
        ]
    """, command_mocks)

    assert command_mocks.execute_forward.call_count == 4


def test_complete_function_using_global_program(command_mocks):
    """A function can read a global variable through the complete pipeline."""
    execute("""
        SET angle 90

        FUNC square size [
            REPEAT 4 [
                FORWARD size
                RIGHT angle
            ]
        ]

        CALL square 50
    """, command_mocks)

    assert command_mocks.execute_right.call_count == 4
    command_mocks.execute_right.assert_any_call(90)


def test_complete_value_returning_function_program(command_mocks):
    """Function return values can feed later drawing commands."""
    interpreter = execute("""
        FUNC double x [
            RETURN x * 2
        ]

        SET size CALL double 50
        FORWARD size
    """, command_mocks)

    assert interpreter.global_env.get_variable("size") == 100
    command_mocks.execute_forward.assert_called_once_with(100)


# ===========================================================================
# Stage boundaries
# ===========================================================================


def test_semantic_error_occurs_before_graphics_initialization(command_mocks):
    """Semantically invalid programs never initialize the turtle backend."""
    with pytest.raises(SemanticError):
        tree, semantic_result = analyze('FORWARD "hello"')
        from Carapace.src.interpreter import Interpreter
        Interpreter(tree, semantic_result).run()

    command_mocks.init_graphics.assert_not_called()


def test_runtime_error_still_finalizes_graphics(command_mocks):
    """Once runtime starts, graphics finalization occurs even when execution fails."""
    with pytest.raises(CarapaceRuntimeError):
        execute("""
            FUNC move x [
                FORWARD x
            ]

            CALL move "bad"
        """, command_mocks)

    command_mocks.init_graphics.assert_called_once_with()
    command_mocks.finish_graphics.assert_called_once_with()


def test_runtime_error_is_not_masked_by_graphics_cleanup(command_mocks):
    """A cleanup failure must not replace the original Carapace runtime error."""
    command_mocks.finish_graphics.side_effect = RuntimeError("cleanup failed")

    with pytest.raises(CarapaceRuntimeError, match="FORWARD requires NUMBER"):
        execute("""
            FUNC move x [
                FORWARD x
            ]

            CALL move "bad"
        """, command_mocks)
