from src.lexer import Lexer, TokenType


def test_tokenizes_assignment_and_number():
    tokens = Lexer("SET x 10").tokenize()

    assert [token.type for token in tokens[:-1]] == [
        TokenType.SET,
        TokenType.IDENTIFIER,
        TokenType.NUMBER,
    ]
    assert tokens[-1].type == TokenType.EOF


def test_tokenizes_math_and_comparison_operators():
    tokens = Lexer("IF x > 5").tokenize()

    assert [token.type for token in tokens[:-1]] == [
        TokenType.IF,
        TokenType.IDENTIFIER,
        TokenType.GT,
        TokenType.NUMBER,
    ]
    assert tokens[-1].type == TokenType.EOF
