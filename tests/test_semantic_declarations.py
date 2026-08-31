import pytest

from Carapace.src.errors import SemanticError
from Carapace.tests.conftest import analyze


# ===========================================================================
# Global function collection
# ===========================================================================


def test_function_can_be_called_before_declaration():
    """Global functions are collected before ordinary statement analysis."""
    analyze("""
        CALL draw

        FUNC draw [
            FORWARD 10
        ]
    """)


def test_function_body_can_call_function_declared_later():
    """Function textual order does not determine visibility."""
    analyze("""
        FUNC first [
            CALL second
        ]

        FUNC second [
            FORWARD 10
        ]
    """)


def test_direct_recursion_is_semantically_valid():
    """A function can resolve its own name during semantic analysis."""
    analyze("""
        FUNC countdown n [
            IF n > 0 [
                CALL countdown n - 1
            ]
        ]
    """)


def test_mutual_recursion_is_semantically_valid():
    """All global function names are known before function bodies are analyzed."""
    analyze("""
        FUNC first n [
            IF n > 0 [
                CALL second n - 1
            ]
        ]

        FUNC second n [
            IF n > 0 [
                CALL first n - 1
            ]
        ]
    """)


# ===========================================================================
# Invalid declarations
# ===========================================================================


def test_duplicate_function_name_is_rejected():
    """Two global functions cannot declare the same name."""
    with pytest.raises(SemanticError, match="draw"):
        analyze("""
            FUNC draw [
            ]

            FUNC draw [
            ]
        """)


def test_duplicate_parameter_is_rejected():
    """A function cannot contain duplicate parameter names."""
    with pytest.raises(SemanticError, match="x"):
        analyze("""
            FUNC test x y x [
                FORWARD x
            ]
        """)


def test_same_parameter_name_in_different_functions_is_valid():
    """Parameter names are local to their own function declarations."""
    analyze("""
        FUNC first x [
            FORWARD x
        ]

        FUNC second x [
            FORWARD x
        ]
    """)


@pytest.mark.parametrize(
    "source",
    [
        """
        FUNC outer [
            FUNC inner [
                FORWARD 10
            ]
        ]
        """,
        """
        IF 1 == 1 [
            FUNC inner [
                FORWARD 10
            ]
        ]
        """,
        """
        REPEAT 1 [
            FUNC inner [
                FORWARD 10
            ]
        ]
        """,
    ],
)
def test_nested_function_declaration_is_rejected(source):
    """FUNC is valid only as a direct child of the program."""
    with pytest.raises(SemanticError):
        analyze(source)


def test_duplicate_function_error_reports_second_declaration_line():
    """Semantic declaration errors use source locations propagated by the parser."""
    with pytest.raises(SemanticError, match=r"Line 5:.*draw"):
        analyze("""FUNC draw [
    FORWARD 10
]

FUNC draw [
    FORWARD 20
]
""")
