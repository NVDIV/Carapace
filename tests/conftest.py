from Carapace.src.lexer import Lexer
from Carapace.src.parser import Parser


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

def analyze(source):
    """Parse source code and perform semantic analysis."""
    from Carapace.src.semantic_analyzer import SemanticAnalyzer

    tree = parse(source)
    semantic_result = SemanticAnalyzer(tree).analyze()
    return tree, semantic_result


import pytest
from unittest.mock import Mock


@pytest.fixture
def command_mocks(monkeypatch):
    """Replace turtle-facing commands with mocks for interpreter tests."""
    import Carapace.src.interpreter as interpreter_module

    mocked = Mock()
    mocked.init_graphics = Mock()
    mocked.finish_graphics = Mock()
    mocked.execute_forward = Mock()
    mocked.execute_backward = Mock()
    mocked.execute_left = Mock()
    mocked.execute_right = Mock()
    mocked.execute_penup = Mock()
    mocked.execute_pendown = Mock()
    mocked.execute_color = Mock()
    mocked.execute_width = Mock()
    mocked.execute_speed = Mock()

    monkeypatch.setattr(interpreter_module, "commands", mocked)
    return mocked
