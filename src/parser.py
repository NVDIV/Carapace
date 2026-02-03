from dataclasses import dataclass
from src.lexer import TokenType, Token
from src.errors import ParserError

##########################################
#   AST NODES (Abstract Syntax Tree)
##########################################

class ASTNode:
    """Base class for all AST nodes."""
    pass

@dataclass
class ForwardNode(ASTNode):
    distance: int

@dataclass
class LeftNode(ASTNode):
    angle: int

@dataclass
class RepeatNode(ASTNode):
    times: int
    body: list[ASTNode] # The body contains a list of other nodes (nested statements)

##########################################
#   PARSER (Recursive Descent)
##########################################

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0 # Current token index

    def current_token(self) -> Token:
        """Returns the token at the current position."""
        return self.tokens[self.pos]

    def consume(self, expected_type: TokenType) -> Token:
        """
        Consumes the current token if it matches the expected type.
        Advances the position pointer. Raises ParserError otherwise.
        """
        token = self.current_token()
        if token.type == expected_type:
            self.pos += 1
            return token
        else:
            raise ParserError(
                f"Line {token.line}: Expected {expected_type.name}, "
                f"but got {token.type.name} ('{token.value}')"
            )

    # RULE: <Program> ::= <Statement>* EOF
    def parse(self) -> list[ASTNode]:
        """Entry point for parsing. Returns the root of the AST (a list of nodes)."""
        statements = []
        
        while self.current_token().type != TokenType.EOF:
            statements.append(self.parse_statement())
            
        return statements

    # RULE: <Statement> ::= <Command> | <Loop>
    def parse_statement(self) -> ASTNode:
        """Determines which type of statement to parse based on the current token."""
        token = self.current_token()

        match token.type:
            case TokenType.FORWARD:
                return self.parse_forward()
            case TokenType.LEFT:
                return self.parse_left()
            case TokenType.REPEAT:
                return self.parse_repeat()
            case _:
                raise ParserError(f"Line {token.line}: Unexpected token {token.type.name}")

    # RULE: <Command> ::= "FORWARD" NUMBER
    def parse_forward(self) -> ASTNode:
        self.consume(TokenType.FORWARD)
        number_token = self.consume(TokenType.NUMBER)
        return ForwardNode(distance=number_token.value)

    # RULE: <Command> ::= "LEFT" NUMBER
    def parse_left(self) -> ASTNode:
        self.consume(TokenType.LEFT)
        number_token = self.consume(TokenType.NUMBER)
        return LeftNode(angle=number_token.value)

    # RULE: <Loop> ::= "REPEAT" NUMBER "[" <Statement>* "]"
    def parse_repeat(self) -> ASTNode:
        # Parse loop header
        self.consume(TokenType.REPEAT)
        times_token = self.consume(TokenType.NUMBER)
        self.consume(TokenType.LBRACKET)

        # Parse loop body
        body = []
        while self.current_token().type != TokenType.RBRACKET:
            if self.current_token().type == TokenType.EOF:
                raise ParserError(f"Line {times_token.line}: Missing closing ']' for REPEAT block")
            
            # Recursion: statements inside the loop
            body.append(self.parse_statement())

        # 3. Consume closing bracket
        self.consume(TokenType.RBRACKET)

        return RepeatNode(times=times_token.value, body=body)