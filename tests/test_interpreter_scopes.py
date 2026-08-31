import pytest

from Carapace.src.errors import RuntimeError as CarapaceRuntimeError
from Carapace.tests.conftest import analyze


def make_interpreter(source):
    """Create an interpreter for already semantically validated source."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    return Interpreter(tree, semantic_result)


# ===========================================================================
# Global and local variables
# ===========================================================================


def test_global_set_stores_runtime_value(command_mocks):
    """Top-level SET writes to GlobalEnvironment."""
    interpreter = make_interpreter("SET x 10")

    interpreter.run()

    assert interpreter.global_env.get_variable("x") == 10


def test_function_local_does_not_leak_to_global_scope(command_mocks):
    """A local variable disappears when its function call finishes."""
    interpreter = make_interpreter("""
        FUNC test [
            SET local 10
        ]

        CALL test
    """)

    interpreter.run()

    assert "local" not in interpreter.global_env.variables


def test_function_reads_global_variable(command_mocks):
    """Runtime lookup falls back from function-local scope to global scope."""
    interpreter = make_interpreter("""
        SET x 10

        FUNC draw [
            FORWARD x
        ]

        CALL draw
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)


def test_local_variable_shadows_global_without_mutating_it(command_mocks):
    """Local SET shadows a global value and leaves the global value unchanged."""
    interpreter = make_interpreter("""
        SET x 10

        FUNC draw [
            SET x 20
            FORWARD x
        ]

        CALL draw
        FORWARD x
    """)

    interpreter.run()

    assert [call.args[0] for call in command_mocks.execute_forward.call_args_list] == [20, 10]
    assert interpreter.global_env.get_variable("x") == 10


def test_parameter_shadows_global_variable(command_mocks):
    """A parameter has the same local-over-global precedence as any local variable."""
    interpreter = make_interpreter("""
        SET x 10

        FUNC draw x [
            FORWARD x
        ]

        CALL draw 20
        FORWARD x
    """)

    interpreter.run()

    assert [call.args[0] for call in command_mocks.execute_forward.call_args_list] == [20, 10]


# ===========================================================================
# Blocks share their enclosing environment
# ===========================================================================


def test_if_assignment_changes_enclosing_global_scope(command_mocks):
    """IF executes in the current environment rather than a child environment."""
    interpreter = make_interpreter("""
        SET x 1

        IF 1 == 1 [
            SET x 2
        ]

        FORWARD x
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("x") == 2
    command_mocks.execute_forward.assert_called_once_with(2)


def test_repeat_assignment_changes_enclosing_function_scope(command_mocks):
    """REPEAT does not create a function-local child scope."""
    interpreter = make_interpreter("""
        FUNC test [
            SET x 1

            REPEAT 1 [
                SET x 2
            ]

            FORWARD x
        ]

        CALL test
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(2)


# ===========================================================================
# Environment restoration
# ===========================================================================


def test_nested_call_restores_caller_environment(command_mocks):
    """After a nested call, execution continues in the caller's local environment."""
    interpreter = make_interpreter("""
        FUNC inner [
            SET inner_value 20
        ]

        FUNC outer [
            SET outer_value 10
            CALL inner
            FORWARD outer_value
        ]

        CALL outer
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)


def test_returning_nested_call_restores_caller_environment(command_mocks):
    """ReturnSignal from a callee does not leave the interpreter in the callee environment."""
    interpreter = make_interpreter("""
        FUNC inner [
            RETURN 42
        ]

        FUNC outer [
            SET x 10
            CALL inner
            FORWARD x
        ]

        CALL outer
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)


def test_runtime_error_restores_previous_environment(command_mocks):
    """The previous environment is restored in finally even when a call fails."""
    interpreter = make_interpreter("""
        FUNC fail x [
            FORWARD x
        ]
    """)

    previous_env = interpreter.env
    function = interpreter.global_env.get_function("fail")

    with pytest.raises(CarapaceRuntimeError):
        interpreter.execute_function_call(
            function_name="fail",
            arguments=[__import__("src.ast", fromlist=["LiteralNode"]).LiteralNode("bad")],
            value_required=False,
        )

    assert interpreter.env is previous_env
