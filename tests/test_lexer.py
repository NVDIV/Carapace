"""
Tests for the Carapace lexer.

The tests in this file intentionally cover both individual token types and
realistic Carapace source fragments.  The lexer is responsible only for
turning source text into tokens; syntax validity belongs to the parser.

Run with:
    pytest -q
"""

import pytest

from Carapace.src.lexer import Lexer, TokenType
from Carapace.src.errors import LexerError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def token_types(source):
    """Return token types for a source string, excluding the EOF token."""
    return [token.type for token in Lexer(source).tokenize() if token.type != TokenType.EOF]


def tokens(source):
    """Tokenize source and return the complete token list, including EOF."""
    return Lexer(source).tokenize()


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------

def test_integer_number_is_tokenized_as_number():
    """A sequence of decimal digits is converted to a NUMBER token."""
    result = tokens("100")

    assert result[0].type == TokenType.NUMBER
    assert result[0].value == 100


def test_zero_is_valid_number():
    """Zero is a valid integer literal and keeps its numeric value."""
    result = tokens("0")

    assert result[0].type == TokenType.NUMBER
    assert result[0].value == 0


def test_multiple_numbers_are_tokenized_separately():
    """Whitespace-separated integer literals become separate NUMBER tokens."""
    result = tokens("10 20 300")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.NUMBER, 10),
        (TokenType.NUMBER, 20),
        (TokenType.NUMBER, 300),
    ]


def test_number_in_turtle_command():
    """A numeric argument following a turtle command is tokenized correctly."""
    result = tokens("FORWARD 100")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.NUMBER, 100),
    ]


def test_number_in_arithmetic_expression():
    """Numbers inside arithmetic expressions are recognized independently."""
    result = tokens("10 + 20 * 3")

    assert token_types("10 + 20 * 3") == [
        TokenType.NUMBER,
        TokenType.PLUS,
        TokenType.NUMBER,
        TokenType.MULTIPLY,
        TokenType.NUMBER,
    ]
    assert [t.value for t in result[:-1]] == [10, "+", 20, "*", 3]


def test_negative_number_is_minus_followed_by_number():
    """Negative literals are lexed as MINUS and NUMBER, not as one NUMBER."""
    result = tokens("-10")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.MINUS, "-"),
        (TokenType.NUMBER, 10),
    ]


def test_leading_zeros_are_accepted_and_converted_to_integer():
    """The current lexer accepts leading zeros and converts the value to int."""
    result = tokens("001")

    assert result[0].type == TokenType.NUMBER
    assert result[0].value == 1


def test_decimal_number_is_rejected():
    """A decimal point is not part of the NUMBER grammar and causes an error."""
    with pytest.raises(LexerError, match=r"Unexpected character '\.'"):
        Lexer("10.5").tokenize()


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "keyword, token_type",
    [
        ("FORWARD", TokenType.FORWARD),
        ("BACKWARD", TokenType.BACKWARD),
        ("LEFT", TokenType.LEFT),
        ("RIGHT", TokenType.RIGHT),
        ("REPEAT", TokenType.REPEAT),
        ("IF", TokenType.IF),
        ("PENUP", TokenType.PENUP),
        ("PENDOWN", TokenType.PENDOWN),
        ("COLOR", TokenType.COLOR),
        ("WIDTH", TokenType.WIDTH),
        ("SPEED", TokenType.SPEED),
        ("SET", TokenType.SET),
        ("FUNC", TokenType.FUNC),
        ("CALL", TokenType.CALL),
        ("RETURN", TokenType.RETURN),
    ],
)
def test_keyword_is_tokenized_with_correct_type(keyword, token_type):
    """Every reserved Carapace keyword maps to its corresponding token type."""
    result = tokens(keyword)

    assert result[0].type == token_type
    assert result[0].value == keyword


@pytest.mark.parametrize(
    "keyword",
    [
        "FORWARD",
        "BACKWARD",
        "LEFT",
        "RIGHT",
        "REPEAT",
        "IF",
        "PENUP",
        "PENDOWN",
        "COLOR",
        "WIDTH",
        "SPEED",
        "SET",
        "FUNC",
        "CALL",
        "RETURN",
    ],
)
def test_keyword_is_case_insensitive(keyword):
    """Keywords are recognized regardless of their letter casing."""
    mixed_case = "".join(
        char.lower() if index % 2 else char.upper()
        for index, char in enumerate(keyword)
    )

    result = tokens(mixed_case)

    assert result[0].type == TokenType[keyword]
    assert result[0].value == keyword


@pytest.mark.parametrize(
    "identifier",
    [
        "FORWARDING",
        "MYFORWARD",
        "SETTER",
        "RETURN_VALUE",
    ],
)
def test_keyword_like_word_is_identifier(identifier):
    """A word containing a keyword as a prefix or part remains an identifier."""
    result = tokens(identifier)

    assert result[0].type == TokenType.IDENTIFIER
    assert result[0].value == identifier


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("identifier", ["x", "size", "foo", "my_variable", "_", "___"])
def test_valid_identifier_is_tokenized_as_identifier(identifier):
    """Alphabetic and underscore-only words are recognized as identifiers."""
    result = tokens(identifier)

    assert result[0].type == TokenType.IDENTIFIER
    assert result[0].value == identifier


def test_identifier_preserves_original_case():
    """Unlike keywords, identifiers keep their original spelling and casing."""
    result = tokens("myVariable")

    assert result[0].type == TokenType.IDENTIFIER
    assert result[0].value == "myVariable"


def test_uppercase_non_keyword_is_identifier():
    """An uppercase word that is not reserved remains an identifier."""
    result = tokens("MYVAR")

    assert result[0].type == TokenType.IDENTIFIER
    assert result[0].value == "MYVAR"


def test_identifier_with_digits_is_split_by_current_lexer_rules():
    """Digits are not allowed by the current identifier regex and start NUMBER."""
    result = tokens("x1")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.IDENTIFIER, "x"),
        (TokenType.NUMBER, 1),
    ]


def test_number_followed_by_identifier_is_tokenized_separately():
    """A number followed immediately by letters becomes NUMBER plus IDENTIFIER."""
    result = tokens("123abc")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.NUMBER, 123),
        (TokenType.IDENTIFIER, "abc"),
    ]


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

def test_simple_string_is_tokenized_without_quotes():
    """A quoted string becomes STRING and its token value excludes the quotes."""
    result = tokens('"red"')

    assert result[0].type == TokenType.STRING
    assert result[0].value == "red"


def test_empty_string_is_valid():
    """An empty pair of quotes produces an empty STRING value."""
    result = tokens('""')

    assert result[0].type == TokenType.STRING
    assert result[0].value == ""


def test_string_with_spaces_is_kept_as_one_token():
    """Spaces inside quotes belong to the string and are not skipped."""
    result = tokens('"hello world"')

    assert result[0].type == TokenType.STRING
    assert result[0].value == "hello world"


def test_string_with_numbers_is_still_string():
    """Digits inside quotes do not become NUMBER tokens."""
    result = tokens('"123"')

    assert result[0].type == TokenType.STRING
    assert result[0].value == "123"


@pytest.mark.parametrize(
    "value",
    [
        "red-blue",
        "hello!",
        "red green",
        "123 / 456",
    ],
)
def test_string_can_contain_non_quote_characters(value):
    """Any characters except a double quote are accepted inside a string."""
    result = tokens(f'"{value}"')

    assert result[0].type == TokenType.STRING
    assert result[0].value == value


def test_unterminated_string_raises_lexer_error():
    """A string without a closing quote cannot be tokenized."""
    with pytest.raises(LexerError, match=r"Unexpected character '\"'"):
        Lexer('"red').tokenize()


def test_quote_inside_string_terminates_string_and_invalidates_remainder():
    """An unescaped quote closes the string; the following unmatched quote errors."""
    with pytest.raises(LexerError, match=r"Unexpected character '\"'"):
        Lexer('"red"blue"').tokenize()


# ---------------------------------------------------------------------------
# Brackets and parentheses
# ---------------------------------------------------------------------------

def test_brackets_are_tokenized():
    """Square brackets become LBRACKET and RBRACKET tokens."""
    result = tokens("[ ]")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.LBRACKET, "["),
        (TokenType.RBRACKET, "]"),
    ]


def test_nested_brackets_are_tokenized_independently():
    """Repeated square brackets are each recognized as separate tokens."""
    result = tokens("[[ ]]")

    assert [t.type for t in result[:-1]] == [
        TokenType.LBRACKET,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.RBRACKET,
    ]


def test_brackets_can_surround_arguments():
    """Numbers inside brackets are tokenized normally."""
    result = tokens("[10 20]")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.LBRACKET, "["),
        (TokenType.NUMBER, 10),
        (TokenType.NUMBER, 20),
        (TokenType.RBRACKET, "]"),
    ]


def test_parentheses_are_tokenized():
    """Round parentheses become LPAREN and RPAREN tokens."""
    result = tokens("( )")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.LPAREN, "("),
        (TokenType.RPAREN, ")"),
    ]


def test_parentheses_in_expression_are_tokenized():
    """Parentheses in an arithmetic expression are recognized correctly."""
    result = tokens("(10 + 20)")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.LPAREN, "("),
        (TokenType.NUMBER, 10),
        (TokenType.PLUS, "+"),
        (TokenType.NUMBER, 20),
        (TokenType.RPAREN, ")"),
    ]


def test_nested_parentheses_are_tokenized():
    """Nested parentheses are represented by repeated LPAREN/RPAREN tokens."""
    result = tokens("((10))")

    assert [t.type for t in result[:-1]] == [
        TokenType.LPAREN,
        TokenType.LPAREN,
        TokenType.NUMBER,
        TokenType.RPAREN,
        TokenType.RPAREN,
    ]


# ---------------------------------------------------------------------------
# Arithmetic operators
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "operator, token_type",
    [
        ("+", TokenType.PLUS),
        ("-", TokenType.MINUS),
        ("*", TokenType.MULTIPLY),
        ("/", TokenType.DIVIDE),
    ],
)
def test_arithmetic_operator_is_tokenized(operator, token_type):
    """Each supported arithmetic operator maps to its correct token type."""
    result = tokens(operator)

    assert result[0].type == token_type
    assert result[0].value == operator


def test_arithmetic_expression_without_spaces_is_tokenized():
    """Operators are recognized even when there is no whitespace between tokens."""
    result = tokens("10+20*3")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.NUMBER, 10),
        (TokenType.PLUS, "+"),
        (TokenType.NUMBER, 20),
        (TokenType.MULTIPLY, "*"),
        (TokenType.NUMBER, 3),
    ]


def test_arithmetic_expression_with_spaces_is_tokenized():
    """Whitespace around arithmetic operators is ignored."""
    result = tokens("10 - 20 / 5")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.NUMBER, 10),
        (TokenType.MINUS, "-"),
        (TokenType.NUMBER, 20),
        (TokenType.DIVIDE, "/"),
        (TokenType.NUMBER, 5),
    ]


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            "++--",
            [
                TokenType.PLUS,
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.MINUS,
            ],
        ),
        (
            "**//",
            [
                TokenType.MULTIPLY,
                TokenType.MULTIPLY,
                TokenType.DIVIDE,
                TokenType.DIVIDE,
            ],
        ),
    ],
)
def test_operator_sequences_are_lexed_without_parser_validation(
    source, expected
):
    """
    The lexer recognizes individual operators even when their sequence
    is syntactically invalid. Syntax validation belongs to the parser.
    """
    result = Lexer(source).tokenize()

    assert [token.type for token in result[:-1]] == expected
    assert result[-1].type == TokenType.EOF

# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "operator, token_type",
    [
        ("==", TokenType.EQ),
        ("<", TokenType.LT),
        (">", TokenType.GT),
    ],
)
def test_comparison_operator_is_tokenized(operator, token_type):
    """Each supported comparison operator maps to the correct token type."""
    result = tokens(operator)

    assert result[0].type == token_type
    assert result[0].value == operator


def test_equality_expression_is_tokenized():
    """An equality expression produces identifier, EQ and NUMBER tokens."""
    result = tokens("x == 10")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.IDENTIFIER, "x"),
        (TokenType.EQ, "=="),
        (TokenType.NUMBER, 10),
    ]


def test_less_than_expression_is_tokenized():
    """A less-than expression produces identifier, LT and NUMBER tokens."""
    result = tokens("x < 10")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.IDENTIFIER, "x"),
        (TokenType.LT, "<"),
        (TokenType.NUMBER, 10),
    ]


def test_greater_than_expression_is_tokenized():
    """A greater-than expression produces identifier, GT and NUMBER tokens."""
    result = tokens("x > 10")

    assert [(t.type, t.value) for t in result[:-1]] == [
        (TokenType.IDENTIFIER, "x"),
        (TokenType.GT, ">"),
        (TokenType.NUMBER, 10),
    ]


def test_single_equals_is_lexer_error():
    """A single '=' is unsupported because Carapace uses '==' for equality."""
    with pytest.raises(LexerError, match=r"Unexpected character '='"):
        Lexer("=").tokenize()


def test_triple_equals_is_lexer_error():
    """'===' is lexed as '==' followed by an invalid single '='."""
    with pytest.raises(LexerError, match=r"Unexpected character '='"):
        Lexer("===").tokenize()


# ---------------------------------------------------------------------------
# Whitespace
# ---------------------------------------------------------------------------

def test_spaces_are_ignored():
    """Spaces separate tokens but do not produce tokens themselves."""
    assert token_types("FORWARD    100") == [
        TokenType.FORWARD,
        TokenType.NUMBER,
    ]


def test_tabs_are_ignored():
    """Tabs are treated as whitespace and do not produce tokens."""
    assert token_types("FORWARD\t100") == [
        TokenType.FORWARD,
        TokenType.NUMBER,
    ]


def test_mixed_spaces_and_tabs_are_ignored():
    """A mixture of spaces and tabs is ignored between tokens."""
    assert token_types("FORWARD \t 100") == [
        TokenType.FORWARD,
        TokenType.NUMBER,
    ]


# ---------------------------------------------------------------------------
# Newlines and line numbers
# ---------------------------------------------------------------------------

def test_newline_does_not_create_token():
    """Newlines advance the line counter but are not included in token output."""
    assert token_types("FORWARD 100\nLEFT 90") == [
        TokenType.FORWARD,
        TokenType.NUMBER,
        TokenType.LEFT,
        TokenType.NUMBER,
    ]


def test_multiple_newlines_advance_line_number():
    """Several consecutive newlines advance the lexer line number accordingly."""
    result = tokens("FORWARD 100\n\n\nLEFT 90")

    assert result[-1].line == 4


def test_empty_lines_do_not_create_tokens():
    """Empty source lines are ignored except for their effect on line numbering."""
    result = tokens("FORWARD 100\n\nLEFT 90")

    assert token_types("FORWARD 100\n\nLEFT 90") == [
        TokenType.FORWARD,
        TokenType.NUMBER,
        TokenType.LEFT,
        TokenType.NUMBER,
    ]
    assert result[2].line == 3


def test_tokens_have_correct_line_numbers():
    """Every non-EOF token records the source line where it was found."""
    result = tokens("FORWARD 100\nLEFT 90\nRIGHT 45")

    assert [(t.value, t.line) for t in result[:-1]] == [
        ("FORWARD", 1),
        (100, 1),
        ("LEFT", 2),
        (90, 2),
        ("RIGHT", 3),
        (45, 3),
    ]


def test_eof_has_correct_line_after_final_newline():
    """EOF is placed on the next line when the source ends with a newline."""
    result = tokens("FORWARD 100\n")

    assert result[-1].type == TokenType.EOF
    assert result[-1].line == 2


def test_error_contains_correct_line_number():
    """A lexical error reports the line on which the invalid character occurs."""
    source = "FORWARD 100\nLEFT 90\n@"

    with pytest.raises(
        LexerError,
        match=r"Line 3: Unexpected character '@'",
    ):
        Lexer(source).tokenize()


def test_windows_crlf_line_endings_are_supported():
    """Windows CRLF line endings are treated as normal newlines."""
    result = tokens("FORWARD 100\r\nLEFT 90")

    assert [(t.type, t.value, t.line) for t in result] == [
        (TokenType.FORWARD, "FORWARD", 1),
        (TokenType.NUMBER, 100, 1),
        (TokenType.LEFT, "LEFT", 2),
        (TokenType.NUMBER, 90, 2),
        (TokenType.EOF, None, 2),
    ]

# ---------------------------------------------------------------------------
# Invalid characters
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "character",
    ["@", "#", "$", "%", "&", "=", "!", "?", ",", ".", ":", ";"],
)
def test_unsupported_ascii_character_raises_lexer_error(character):
    """Any unsupported ASCII character is rejected by the MISMATCH rule."""
    with pytest.raises(LexerError):
        Lexer(character).tokenize()


def test_unicode_character_is_rejected():
    """Non-ASCII letters are not valid WORD characters in the current lexer."""
    with pytest.raises(LexerError):
        Lexer("привет").tokenize()


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def test_hash_comment_is_not_supported():
    """
    Comments are not part of the current lexer.

    Therefore '#' is an invalid character rather than the start of a comment.
    """
    with pytest.raises(LexerError, match=r"Unexpected character '#'"):
        Lexer("# comment").tokenize()


# ---------------------------------------------------------------------------
# Empty input and EOF
# ---------------------------------------------------------------------------

def test_empty_input_produces_only_eof():
    """An empty source file produces exactly one token: EOF."""
    result = tokens("")

    assert len(result) == 1
    assert result[0].type == TokenType.EOF


def test_empty_input_eof_is_on_line_one():
    """EOF for empty input is located on the initial line."""
    result = tokens("")

    assert result[0].line == 1


def test_whitespace_only_input_produces_only_eof():
    """Input containing only spaces and tabs produces no regular tokens."""
    result = tokens("   \t   ")

    assert len(result) == 1
    assert result[0].type == TokenType.EOF


def test_newline_only_input_produces_only_eof():
    """Newlines produce no tokens while still advancing the line counter."""
    result = tokens("\n\n\n")

    assert len(result) == 1
    assert result[0].type == TokenType.EOF
    assert result[0].line == 4


def test_eof_is_always_the_last_token():
    """The lexer always appends exactly one EOF token at the end."""
    result = tokens("FORWARD 100")

    assert result[-1].type == TokenType.EOF
    assert all(token.type != TokenType.EOF for token in result[:-1])


def test_eof_value_is_none():
    """EOF has no source value."""
    result = tokens("FORWARD")

    assert result[-1].value is None


# ---------------------------------------------------------------------------
# Token values
# ---------------------------------------------------------------------------

def test_keyword_value_is_uppercase():
    """A keyword token stores its canonical uppercase spelling."""
    result = tokens("forward")

    assert result[0].type == TokenType.FORWARD
    assert result[0].value == "FORWARD"


def test_identifier_value_preserves_spelling():
    """Identifier values retain their exact source spelling."""
    result = tokens("myVar")

    assert result[0].value == "myVar"


def test_number_value_is_integer():
    """NUMBER token values are converted from strings to Python integers."""
    result = tokens("123")

    assert result[0].value == 123
    assert isinstance(result[0].value, int)


def test_string_value_excludes_quotes():
    """STRING token values contain only the characters between the quotes."""
    result = tokens('"red"')

    assert result[0].value == "red"


# ---------------------------------------------------------------------------
# Realistic Carapace programs
# ---------------------------------------------------------------------------

def test_simple_turtle_program():
    """A basic drawing program produces the expected complete token sequence."""
    result = tokens(
        "FORWARD 100\n"
        "LEFT 90\n"
        "FORWARD 100"
    )

    assert [(t.type, t.value) for t in result] == [
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.NUMBER, 100),
        (TokenType.LEFT, "LEFT"),
        (TokenType.NUMBER, 90),
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.NUMBER, 100),
        (TokenType.EOF, None),
    ]


def test_variable_program():
    """SET and a variable reference are both lexed correctly."""
    result = tokens(
        "SET size 100\n"
        "FORWARD size"
    )

    assert [(t.type, t.value) for t in result] == [
        (TokenType.SET, "SET"),
        (TokenType.IDENTIFIER, "size"),
        (TokenType.NUMBER, 100),
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.IDENTIFIER, "size"),
        (TokenType.EOF, None),
    ]


def test_repeat_program():
    """A REPEAT block with brackets and commands is lexed as one token stream."""
    result = tokens(
        "REPEAT 4 [\n"
        "    FORWARD 100\n"
        "    RIGHT 90\n"
        "]"
    )

    assert [(t.type, t.value) for t in result] == [
        (TokenType.REPEAT, "REPEAT"),
        (TokenType.NUMBER, 4),
        (TokenType.LBRACKET, "["),
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.NUMBER, 100),
        (TokenType.RIGHT, "RIGHT"),
        (TokenType.NUMBER, 90),
        (TokenType.RBRACKET, "]"),
        (TokenType.EOF, None),
    ]


def test_if_program():
    """An IF condition containing a comparison and block is lexed correctly."""
    result = tokens(
        "SET x 10\n"
        "IF x > 5 [\n"
        "    FORWARD x\n"
        "]"
    )

    assert [(t.type, t.value) for t in result] == [
        (TokenType.SET, "SET"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.NUMBER, 10),
        (TokenType.IF, "IF"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.GT, ">"),
        (TokenType.NUMBER, 5),
        (TokenType.LBRACKET, "["),
        (TokenType.FORWARD, "FORWARD"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.RBRACKET, "]"),
        (TokenType.EOF, None),
    ]


def test_function_program():
    """A function declaration, call, SET, expression and RETURN are lexed correctly."""
    result = tokens(
        "FUNC test x [\n"
        "    SET y x + 10\n"
        "    RETURN y\n"
        "]\n"
        "CALL test 20"
    )

    assert [(t.type, t.value) for t in result] == [
        (TokenType.FUNC, "FUNC"),
        (TokenType.IDENTIFIER, "test"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.LBRACKET, "["),
        (TokenType.SET, "SET"),
        (TokenType.IDENTIFIER, "y"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.PLUS, "+"),
        (TokenType.NUMBER, 10),
        (TokenType.RETURN, "RETURN"),
        (TokenType.IDENTIFIER, "y"),
        (TokenType.RBRACKET, "]"),
        (TokenType.CALL, "CALL"),
        (TokenType.IDENTIFIER, "test"),
        (TokenType.NUMBER, 20),
        (TokenType.EOF, None),
    ]


def test_complex_arithmetic_expression():
    """Nested arithmetic expressions are tokenized without applying precedence."""
    result = tokens("(10 + 20) * 3 - 5 / 2")

    assert [(t.type, t.value) for t in result] == [
        (TokenType.LPAREN, "("),
        (TokenType.NUMBER, 10),
        (TokenType.PLUS, "+"),
        (TokenType.NUMBER, 20),
        (TokenType.RPAREN, ")"),
        (TokenType.MULTIPLY, "*"),
        (TokenType.NUMBER, 3),
        (TokenType.MINUS, "-"),
        (TokenType.NUMBER, 5),
        (TokenType.DIVIDE, "/"),
        (TokenType.NUMBER, 2),
        (TokenType.EOF, None),
    ]


# ---------------------------------------------------------------------------
# Lexer/parser responsibility boundary
# ---------------------------------------------------------------------------

def test_lexically_valid_but_syntactically_invalid_expression_is_tokenized():
    """
    The lexer recognizes every individual symbol in an invalid expression.

    The sequence '10 + * 20' is syntactically invalid, but lexical analysis
    should still succeed. The parser is responsible for rejecting it.
    """
    result = tokens("10 + * 20")

    assert [(t.type, t.value) for t in result] == [
        (TokenType.NUMBER, 10),
        (TokenType.PLUS, "+"),
        (TokenType.MULTIPLY, "*"),
        (TokenType.NUMBER, 20),
        (TokenType.EOF, None),
    ]


def test_lexer_does_not_check_matching_brackets():
    """
    The lexer only recognizes brackets; it does not validate their structure.

    A missing closing bracket is a parser error, not a lexer error.
    """
    result = tokens("[ FORWARD 100")

    assert [t.type for t in result] == [
        TokenType.LBRACKET,
        TokenType.FORWARD,
        TokenType.NUMBER,
        TokenType.EOF,
    ]
