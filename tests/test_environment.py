import pytest

from Carapace.src.environment import GlobalEnvironment, FunctionEnvironment
from Carapace.src.errors import RuntimeError as CarapaceRuntimeError


# ===========================================================================
# Global environment
# ===========================================================================


def test_global_environment_stores_variable():
    """GlobalEnvironment stores and returns global variable values."""
    env = GlobalEnvironment()

    env.set_variable("x", 10)

    assert env.get_variable("x") == 10


def test_global_environment_updates_variable():
    """Assigning the same global variable again replaces its previous value."""
    env = GlobalEnvironment()
    env.set_variable("x", 10)

    env.set_variable("x", 20)

    assert env.get_variable("x") == 20


def test_global_environment_rejects_unknown_variable():
    """Reading a missing global variable raises a Carapace runtime error."""
    env = GlobalEnvironment()

    with pytest.raises(CarapaceRuntimeError, match="x"):
        env.get_variable("x")


# ===========================================================================
# Global functions
# ===========================================================================


def test_global_environment_stores_function():
    """Functions are stored in the global environment."""
    env = GlobalEnvironment()
    function = object()

    env.define_function("draw", function)

    assert env.get_function("draw") is function


def test_global_environment_rejects_unknown_function():
    """Reading a missing function raises a Carapace runtime error defensively."""
    env = GlobalEnvironment()

    with pytest.raises(CarapaceRuntimeError, match="draw"):
        env.get_function("draw")


# ===========================================================================
# Function environment
# ===========================================================================


def test_function_environment_stores_local_variable():
    """FunctionEnvironment stores variables locally."""
    global_env = GlobalEnvironment()
    env = FunctionEnvironment(parent=global_env)

    env.set_variable("x", 10)

    assert env.get_variable("x") == 10
    assert "x" not in global_env.variables


def test_function_environment_reads_global_variable():
    """A function reads a global value when the name is not defined locally."""
    global_env = GlobalEnvironment()
    global_env.set_variable("x", 10)
    env = FunctionEnvironment(parent=global_env)

    assert env.get_variable("x") == 10


def test_local_variable_shadows_global_variable():
    """Local lookup has priority over a global variable with the same name."""
    global_env = GlobalEnvironment()
    global_env.set_variable("x", 10)
    env = FunctionEnvironment(parent=global_env)
    env.set_variable("x", 20)

    assert env.get_variable("x") == 20
    assert global_env.get_variable("x") == 10


def test_local_assignment_does_not_mutate_global_variable():
    """SET semantics are local: assigning a local name never updates its global shadow."""
    global_env = GlobalEnvironment()
    global_env.set_variable("x", 10)
    env = FunctionEnvironment(parent=global_env)

    env.set_variable("x", 20)

    assert global_env.get_variable("x") == 10


def test_function_environment_parent_is_global_environment():
    """Every function environment points directly to the global environment."""
    global_env = GlobalEnvironment()
    env = FunctionEnvironment(parent=global_env)

    assert env.parent is global_env


def test_callee_environment_does_not_see_caller_local_variable():
    """Caller-local variables are not part of the callee's lookup chain."""
    global_env = GlobalEnvironment()
    caller = FunctionEnvironment(parent=global_env)
    caller.set_variable("secret", 42)

    callee = FunctionEnvironment(parent=global_env)

    with pytest.raises(CarapaceRuntimeError, match="secret"):
        callee.get_variable("secret")


def test_function_environment_does_not_own_functions():
    """Function definitions belong exclusively to GlobalEnvironment."""
    global_env = GlobalEnvironment()
    env = FunctionEnvironment(parent=global_env)

    assert not hasattr(env, "define_function")
    assert not hasattr(env, "functions")
