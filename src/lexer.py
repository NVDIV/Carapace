import re
from dataclasses import dataclass
from enum import Enum, auto
from src.errors import LexerError

##########################################
#   TOKENS
##########################################

class TokenType(Enum):
    # Keywords
    FORWARD = auto()    # Move forward
    BACKWARD = auto()   # Move backward
    LEFT = auto()       # Turn left
    RIGHT = auto()      # Turn right
    REPEAT = auto()     # Instruction Cycle
    PENUP = auto();     # Pen up
    PENDOWN = auto()    # Pen down
    COLOR = auto();     # Pen color
    WIDTH = auto();     # Pen width
    SPEED = auto()      # Speed of the turtle
    SET = auto()        # Variable declaration
    
    # Numbers and literals
    NUMBER = auto()     # Numeric values (e.g., 100)
    STRING = auto()     # Strings like "red"
    IDENTIFIER = auto() # Variable identifier (x, size)

    # Symbols
    LBRACKET = auto()   # [  
    RBRACKET = auto()   # ]  
    
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
    "BACKWARD": TokenType.BACKWARD,
    "LEFT": TokenType.LEFT,
    "RIGHT": TokenType.RIGHT,
    "REPEAT": TokenType.REPEAT,
    "PENUP": TokenType.PENUP, 
    "PENDOWN": TokenType.PENDOWN,
    "COLOR": TokenType.COLOR, 
    "WIDTH": TokenType.WIDTH, 
    "SPEED": TokenType.SPEED,
    "SET": TokenType.SET,
}

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
            ('STRING',   r'"[^"]*"'),       # Strings (in " ")
            ('NEWLINE',  r'\n'),            # Line breaks
            ('LBRACKET', r'\['),            # Left bracket
            ('RBRACKET', r'\]'),            # Rught bracket
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
                    word_value = value.upper()
                    token_type = KEYWORDS.get(word_value)

                    if token_type:
                        tokens.append(Token(token_type, word_value, self.line))
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, value, self.line))

                case 'STRING':
                    clean_value = value.strip('"')
                    tokens.append(Token(TokenType.STRING, clean_value, self.line))
                    
                case 'LBRACKET':
                    tokens.append(Token(TokenType.LBRACKET, "[", self.line))

                case 'RBRACKET':
                    tokens.append(Token(TokenType.RBRACKET, "]", self.line))
                
                case 'NEWLINE':
                    self.line += 1
                
                case 'SKIP':
                    pass # Ignore whitespace
                
                case 'MISMATCH':
                    raise LexerError(f"Line {self.line}: Unexpected character '{value}'")

        # Append End-Of-File token
        tokens.append(Token(TokenType.EOF, line=self.line))
        return tokens