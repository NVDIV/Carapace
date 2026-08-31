import pytest

from Carapace.src.errors import SemanticError
from Carapace.tests.conftest import analyze


# ===========================================================================
# Global variables
# ===========================================================================


def test_global_variable_is_visible_after_set():
    """A top-level variable can be read after its SET statement."""
    analyze("""
        SET x 10
        FORWARD x
    """)


def test_undefined_global_variable_is_rejected():
    """A name that is never declared is a semantic error."""
    with pytest.raises(SemanticError, match="x"):
        analyze("FORWARD x")


def test_top_level_variable_use_before_set_is_rejected():
    """Top-level statements are analyzed sequentially for variable availability."""
    with pytest.raises(SemanticError, match="x"):
        analyze("""
            FORWARD x
            SET x 10
        """)


# ===========================================================================
# Function scopes
# ===========================================================================


def test_global_variable_symbol_is_visible_inside_function():
    """Function semantic lookup falls back from local scope to global scope."""
    analyze("""
        SET distance 10

        FUNC draw [
            FORWARD distance
        ]

        CALL draw
    """)


def test_parameter_is_visible_inside_function():
    """Function parameters are local symbols available throughout the function body."""
    analyze("""
        FUNC draw distance [
            FORWARD distance
        ]
    """)


def test_local_variable_is_visible_later_in_function():
    """A local SET introduces a function-local variable symbol."""
    analyze("""
        FUNC draw [
            SET distance 10
            FORWARD distance
        ]
    """)


def test_local_variable_may_shadow_global_variable():
    """A local variable may use the same name as a global variable."""
    analyze("""
        SET x 10

        FUNC draw [
            SET x 20
            FORWARD x
        ]
    """)


def test_same_local_name_may_exist_in_different_functions():
    """Different function scopes may independently declare the same local name."""
    analyze("""
        FUNC first [
            SET x 10
            FORWARD x
        ]

        FUNC second [
            SET x 20
            FORWARD x
        ]
    """)


def test_caller_local_is_not_visible_to_callee():
    """A callee is analyzed against its own scope and the global scope only."""
    with pytest.raises(SemanticError, match="x"):
        analyze("""
            FUNC callee [
                FORWARD x
            ]

            FUNC caller [
                SET x 100
                CALL callee
            ]

            CALL caller
        """)


# ===========================================================================
# Blocks do not create scopes
# ===========================================================================


def test_variable_set_inside_if_belongs_to_enclosing_scope():
    """IF does not create a semantic child scope."""
    analyze("""
        FUNC test flag [
            IF flag > 0 [
                SET x 10
            ]

            FORWARD x
        ]
    """)


def test_variable_set_inside_repeat_belongs_to_enclosing_scope():
    """REPEAT does not create a semantic child scope."""
    analyze("""
        FUNC test count [
            REPEAT count [
                SET x 10
            ]

            FORWARD x
        ]
    """)


def test_undefined_variable_error_reports_usage_line():
    """Variable errors point to the AST node where the invalid read occurs."""
    with pytest.raises(SemanticError, match=r"Line 2:.*missing"):
        analyze("""SET x 10
FORWARD missing
""")


def test_if_type_change_degrades_existing_variable_to_unknown():
    """A conditional assignment cannot overwrite a pre-block type fact unconditionally."""
    analyze("""
        SET x 10

        IF 1 == 0 [
            SET x "red"
        ]

        FORWARD x
    """)


def test_repeat_type_change_degrades_existing_variable_to_unknown():
    """A loop that may execute zero times makes conflicting post-loop type knowledge UNKNOWN."""
    analyze("""
        SET x 10

        REPEAT 0 [
            SET x "red"
        ]

        FORWARD x
    """)
