import re
from dataclasses import dataclass
from enum import Enum, auto

##########################################
#   TOKENS
##########################################

class TokenType(Enum):
    # Keywords
    FORWARD = auto() # Move forward
    LEFT = auto()    # Turn left
    PENUP = auto()   # Lift the pen up
    
    # Literals
    NUMBER = auto()  # Numeric values (e.g., 100)
    
    # End of file indicator
    EOF = auto()     

@dataclass
class Token:
    type: TokenType
    value: any = None
    line: int = 1

    def __repr__(self):
        # String representation for debugging
        return f"Token({self.type.name}, {self.value})"

# Mapping string literals to Token types
KEYWORDS = {
    "FORWARD": TokenType.FORWARD,
    "LEFT": TokenType.LEFT,
    "PENUP": TokenType.PENUP,
}

##########################################
#   ERRORS
##########################################

class LexerError(Exception):
    """Custom exception class for Lexer errors."""
    pass

##########################################
#   LEXER
##########################################

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.line = 1

    def tokenize(self) -> list[Token]:
        tokens = []
        
        # Regular expression patterns for each token type
        token_specification = [
            ('NUMBER',   r'\d+'),           # Integer numbers
            ('WORD',     r'[A-Za-z_]+'),    # Commands (letters)
            ('NEWLINE',  r'\n'),            # Line breaks
            ('SKIP',     r'[ \t]+'),        # Spaces and tabs
            ('MISMATCH', r'.'),             # Any other character (error)
        ]
        
        # Combine patterns into a single Regex string using named groups
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

        # Iterate through all matches in the source text
        for match in re.finditer(tok_regex, self.text):
            kind = match.lastgroup # Name of the matched pattern (e.g., 'NUMBER')
            value = match.group()  # The actual text matched (e.g., '100')

            match kind:
                case 'NUMBER':
                    tokens.append(Token(TokenType.NUMBER, int(value), self.line))
                
                case 'WORD':
                    # Check if the word is a known command
                    token_type = KEYWORDS.get(value.upper())
                    if not token_type:
                        raise LexerError(f"Line {self.line}: Unknown command '{value}'")
                    tokens.append(Token(token_type, value.upper(), self.line))
                
                case 'NEWLINE':
                    self.line += 1
                
                case 'SKIP':
                    pass # Ignore whitespace
                
                case 'MISMATCH':
                    raise LexerError(f"Line {self.line}: Unexpected character '{value}'")

        # Append End-Of-File token
        tokens.append(Token(TokenType.EOF, line=self.line))
        return tokens