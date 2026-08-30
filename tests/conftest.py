from src.lexer import Lexer
from src.parser import Parser


def parse(source):
    """Tokenize source code and parse it into an Abstract Syntax Tree."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return Parser(tokens).parse()


def parse_one(source):
    """Parse source code and return the only AST node."""
    result = parse(source)

    assert len(result) == 1

    return result[0]