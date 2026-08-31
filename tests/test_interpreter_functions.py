from Carapace.tests.conftest import analyze


def make_interpreter(source):
    """Create an interpreter from semantically valid source."""
    from Carapace.src.interpreter import Interpreter

    tree, semantic_result = analyze(source)
    return Interpreter(tree, semantic_result)


# ===========================================================================
# Parameters and arguments
# ===========================================================================


def test_function_parameter_is_bound_to_argument(command_mocks):
    """A function receives the evaluated argument through its parameter."""
    interpreter = make_interpreter("""
        FUNC move distance [
            FORWARD distance
        ]

        CALL move 100
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(100)


def test_multiple_parameters_are_bound_in_order(command_mocks):
    """Arguments are bound to parameters from left to right."""
    interpreter = make_interpreter("""
        FUNC move distance angle [
            FORWARD distance
            RIGHT angle
        ]

        CALL move 100 90
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(100)
    command_mocks.execute_right.assert_called_once_with(90)


def test_argument_expression_is_evaluated_in_caller_environment(command_mocks):
    """Argument expressions are evaluated before switching to the callee environment."""
    interpreter = make_interpreter("""
        SET x 10

        FUNC move distance [
            FORWARD distance
        ]

        CALL move x + 5
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(15)


def test_caller_local_can_be_passed_explicitly_to_callee(command_mocks):
    """Caller locals are invisible directly but can be transferred as argument values."""
    interpreter = make_interpreter("""
        FUNC inner value [
            FORWARD value
        ]

        FUNC outer [
            SET local 100
            CALL inner local
        ]

        CALL outer
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(100)


# ===========================================================================
# Return behavior
# ===========================================================================


def test_statement_call_may_finish_without_return(command_mocks):
    """Procedure-like functions are valid in statement context."""
    interpreter = make_interpreter("""
        FUNC draw [
            FORWARD 10
        ]

        CALL draw
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(10)


def test_return_value_is_discarded_in_statement_context(command_mocks):
    """A value-returning function can be called for side effects only."""
    interpreter = make_interpreter("""
        FUNC answer [
            RETURN 42
        ]

        CALL answer
    """)

    interpreter.run()


def test_expression_call_assigns_returned_value(command_mocks):
    """A function return value can be consumed by SET."""
    interpreter = make_interpreter("""
        FUNC double x [
            RETURN x * 2
        ]

        SET result CALL double 5
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("result") == 10


def test_return_stops_remaining_function_body(command_mocks):
    """Statements after an executed RETURN are not executed."""
    interpreter = make_interpreter("""
        FUNC answer [
            RETURN 42
            FORWARD 100
        ]

        SET result CALL answer
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("result") == 42
    command_mocks.execute_forward.assert_not_called()


def test_return_inside_if_exits_whole_function(command_mocks):
    """RETURN propagates through IF to the active function boundary."""
    interpreter = make_interpreter("""
        FUNC answer [
            IF 1 == 1 [
                RETURN 42
            ]

            FORWARD 100
        ]

        SET result CALL answer
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("result") == 42
    command_mocks.execute_forward.assert_not_called()


def test_return_inside_repeat_exits_whole_function(command_mocks):
    """RETURN propagates through REPEAT rather than only stopping the loop body."""
    interpreter = make_interpreter("""
        FUNC answer [
            REPEAT 5 [
                RETURN 42
            ]

            FORWARD 100
        ]

        SET result CALL answer
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("result") == 42
    command_mocks.execute_forward.assert_not_called()


# ===========================================================================
# Recursion
# ===========================================================================


def test_direct_recursion_uses_independent_parameter_values(command_mocks):
    """Each recursive call owns a fresh FunctionEnvironment."""
    interpreter = make_interpreter("""
        FUNC countdown n [
            IF n > 0 [
                FORWARD n
                CALL countdown n - 1
            ]
        ]

        CALL countdown 3
    """)

    interpreter.run()

    assert [call.args[0] for call in command_mocks.execute_forward.call_args_list] == [3, 2, 1]


def test_mutual_recursion_works(command_mocks):
    """Globally collected declarations allow mutually recursive calls."""
    interpreter = make_interpreter("""
        FUNC even n [
            IF n == 0 [
                RETURN 1
            ]

            RETURN CALL odd n - 1
        ]

        FUNC odd n [
            IF n == 0 [
                RETURN 0
            ]

            RETURN CALL even n - 1
        ]

        SET result CALL even 4
    """)

    interpreter.run()

    assert interpreter.global_env.get_variable("result") == 1


def test_function_can_execute_before_textual_declaration(command_mocks):
    """Runtime function registration is independent of source declaration order."""
    interpreter = make_interpreter("""
        CALL draw 25

        FUNC draw size [
            FORWARD size
        ]
    """)

    interpreter.run()

    command_mocks.execute_forward.assert_called_once_with(25)
