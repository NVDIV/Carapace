##########################################
#   CARAPACE ERRORS
##########################################

class CarapaceError(Exception):
    """Base class for all errors"""
    pass

class LexerError(CarapaceError):
    """Lexical error (e. g. undefined symbol)"""
    pass

class ParserError(CarapaceError):
    """Syntax error (e. g. no closing bracket found)"""
    pass

class RuntimeError(CarapaceError):
    """Error while drawning"""
    pass