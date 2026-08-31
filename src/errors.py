"""Public Carapace errors and internal interpreter control-flow signals."""


class CarapaceError(Exception):
    """Base class for all user-facing Carapace errors."""


class SourceFileError(CarapaceError):
    """Error while locating, validating or reading a Carapace source file."""


class LexerError(CarapaceError):
    """Lexical error, for example an unsupported source character."""


class ParserError(CarapaceError):
    """Syntactic error in the token stream."""


class SemanticError(CarapaceError):
    """Statically detectable violation of Carapace language semantics."""


class RuntimeError(CarapaceError):
    """Execution-dependent Carapace program error."""


class ReturnSignal(Exception):
    """Internal non-error control flow used to implement RETURN."""

    def __init__(self, value):
        """Store the value being propagated to the function-call boundary."""
        super().__init__()
        self.value = value
