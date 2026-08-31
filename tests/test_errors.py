from Carapace.src.errors import (
    CarapaceError,
    SourceFileError,
    LexerError,
    ParserError,
    SemanticError,
    RuntimeError,
    ReturnSignal,
)


# ===========================================================================
# Public error hierarchy
# ===========================================================================


def test_source_file_error_is_carapace_error():
    """Source-file failures belong to the public Carapace error hierarchy."""
    assert issubclass(SourceFileError, CarapaceError)


def test_lexer_error_is_carapace_error():
    """LexerError is a public Carapace language error."""
    assert issubclass(LexerError, CarapaceError)


def test_parser_error_is_carapace_error():
    """ParserError is a public Carapace language error."""
    assert issubclass(ParserError, CarapaceError)


def test_semantic_error_is_carapace_error():
    """SemanticError is a public Carapace language error."""
    assert issubclass(SemanticError, CarapaceError)


def test_runtime_error_is_carapace_error():
    """RuntimeError is a public Carapace language error."""
    assert issubclass(RuntimeError, CarapaceError)


def test_return_signal_is_not_carapace_error():
    """RETURN is internal control flow and must never be classified as a user error."""
    assert not issubclass(ReturnSignal, CarapaceError)


def test_return_signal_preserves_returned_value():
    """ReturnSignal carries the exact runtime value produced by RETURN."""
    signal = ReturnSignal(42)

    assert signal.value == 42
