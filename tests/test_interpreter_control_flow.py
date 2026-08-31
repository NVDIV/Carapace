from Carapace.tests.conftest import analyze


def make_interpreter(source):
    """Create an interpreter from semantically valid source."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    return Interpreter(tree, semantic_result)


# ===========================================================================
# REPEAT
# ===========================================================================


def test_repeat_executes_body_requested_number_of_times(command_mocks):
    """REPEAT executes its body exactly count times."""
    interpreter = make_interpreter("""
        REPEAT 3 [
            FORWARD 10
        ]
    """)

    interpreter.run()

    assert command_mocks.execute_forward.call_count == 3


def test_repeat_zero_skips_body(command_mocks):
    """REPEAT 0 performs no body executions."""
    interpreter = make_interpreter("""
        REPEAT 0 [
            FORWARD 10
        ]
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_not_called()


def test_nested_repeat_preserves_execution_order(command_mocks):
    """Nested loops execute normally in the same current environment."""
    interpreter = make_interpreter("""
        REPEAT 2 [
            FORWARD 10
            REPEAT 2 [
                RIGHT 90
            ]
        ]
    """)

    interpreter.run()

    assert command_mocks.execute_forward.call_count == 2
    assert command_mocks.execute_right.call_count == 4


# ===========================================================================
# IF
# ===========================================================================


def test_if_true_executes_body(command_mocks):
    """A true comparison executes the IF body."""
    interpreter = make_interpreter("""
        IF 10 < 20 [
            FORWARD 10
        ]
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)


def test_if_false_skips_body(command_mocks):
    """A false comparison skips the IF body."""
    interpreter = make_interpreter("""
        IF 20 < 10 [
            FORWARD 10
        ]
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_not_called()


def test_equality_comparison_works_for_strings(command_mocks):
    """Same-type scalar equality follows the documented comparison semantics."""
    interpreter = make_interpreter("""
        IF "red" == "red" [
            FORWARD 10
        ]
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)
