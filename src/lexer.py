"""Lexical analysis for the Carapace language.

The lexer converts raw source text into a stream of typed tokens while
preserving source line numbers for later diagnostics. Keywords are
case-insensitive; identifier spelling is preserved exactly as written.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto

from Carapace.src.errors import LexerError


class TokenType(Enum):
    """All token categories recognized by the Carapace lexer."""

    # Keywords
    FUNC = auto()
    CALL = auto()
    RETURN = auto()
    IF = auto()
    SET = auto()
    REPEAT = auto()
    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()
    PENUP = auto()
    PENDOWN = auto()
    COLOR = auto()
    WIDTH = auto()
    SPEED = auto()

    # Literals and identifiers
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Delimiters and operators
    LBRACKET = auto()
    RBRACKET = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    LPAREN = auto()
    RPAREN = auto()
    EQ = auto()
    LT = auto()
    GT = auto()

    # End of input
    EOF = auto()


@dataclass
class Token:
    """One lexical token with its value and source line."""

    type: TokenType
    value: any = None
    line: int = 1

    def __repr__(self):
        """Return a compact representation useful during debugging."""
        return f"Token({self.type.name}, {self.value})"


# Case-insensitive keyword lookup. Non-keyword words become IDENTIFIER tokens.
KEYWORDS = {
    "FORWARD": TokenType.FORWARD,
    "BACKWARD": TokenType.BACKWARD,
    "LEFT": TokenType.LEFT,
    "RIGHT": TokenType.RIGHT,
    "REPEAT": TokenType.REPEAT,
    "IF": TokenType.IF,
    "PENUP": TokenType.PENUP,
    "PENDOWN": TokenType.PENDOWN,
    "COLOR": TokenType.COLOR,
    "WIDTH": TokenType.WIDTH,
    "SPEED": TokenType.SPEED,
    "SET": TokenType.SET,
    "FUNC": TokenType.FUNC,
    "CALL": TokenType.CALL,
    "RETURN": TokenType.RETURN,
}


class Lexer:
    """Convert Carapace source text into a sequence of :class:`Token` objects."""

    def __init__(self, text: str):
        """Initialize lexical state for one source string."""
        self.text = text
        self.line = 1

    def tokenize(self) -> list[Token]:
        """Tokenize the complete source and append a final EOF token."""
        tokens = []

        token_specification = [
            ("NUMBER", r"\d+"),
            ("WORD", r"[A-Za-z_]+"),
            ("STRING", r'"[^"]*"'),
            ("NEWLINE", r"\r?\n"),
            ("LBRACKET", r"\["),
            ("RBRACKET", r"\]"),
            ("PLUS", r"\+"),
            ("MINUS", r"-"),
            ("MUL", r"\*"),
            ("DIV", r"/"),
            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("EQ", r"=="),
            ("LT", r"<"),
            ("GT", r">"),
            ("SKIP", r"[ \t]+"),
            ("MISMATCH", r"."),
        ]

        tok_regex = "|".join(
            f"(?P<{name}>{pattern})" for name, pattern in token_specification
        )

        for match in re.finditer(tok_regex, self.text):
            kind = match.lastgroup
            value = match.group()

            match kind:
                case "NUMBER":
                    tokens.append(Token(TokenType.NUMBER, int(value), self.line))

                case "WORD":
                    word_value = value.upper()
                    token_type = KEYWORDS.get(word_value)

                    if token_type:
                        tokens.append(Token(token_type, word_value, self.line))
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, value, self.line))

                case "STRING":
                    clean_value = value.strip('"')
                    tokens.append(Token(TokenType.STRING, clean_value, self.line))

                case "LBRACKET":
                    tokens.append(Token(TokenType.LBRACKET, "[", self.line))

                case "RBRACKET":
                    tokens.append(Token(TokenType.RBRACKET, "]", self.line))

                case "PLUS":
                    tokens.append(Token(TokenType.PLUS, "+", self.line))
                case "MINUS":
                    tokens.append(Token(TokenType.MINUS, "-", self.line))
                case "MUL":
                    tokens.append(Token(TokenType.MULTIPLY, "*", self.line))
                case "DIV":
                    tokens.append(Token(TokenType.DIVIDE, "/", self.line))
                case "LPAREN":
                    tokens.append(Token(TokenType.LPAREN, "(", self.line))
                case "RPAREN":
                    tokens.append(Token(TokenType.RPAREN, ")", self.line))

                case "EQ":
                    tokens.append(Token(TokenType.EQ, "==", self.line))
                case "LT":
                    tokens.append(Token(TokenType.LT, "<", self.line))
                case "GT":
                    tokens.append(Token(TokenType.GT, ">", self.line))

                case "NEWLINE":
                    self.line += 1

                case "SKIP":
                    pass

                case "MISMATCH":
                    raise LexerError(
                        f"Line {self.line}: Unexpected character '{value}'"
                    )

        tokens.append(Token(TokenType.EOF, line=self.line))
        return tokens
