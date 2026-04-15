from dataclasses import dataclass
from src.lexer import TokenType, Token
from src.errors import ParserError

##########################################
#   AST NODES (Abstract Syntax Tree)
##########################################

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    pass

@dataclass
class LiteralNode(ASTNode):
    """Represents a constant value (Number or String)."""
    value: any

@dataclass
class VariableNode(ASTNode):
    """Represents a variable reference by its name."""
    name: str

@dataclass
class SetNode(ASTNode):
    """Represents a variable assignment: SET <name> <expression>."""
    name: str
    value: ASTNode

@dataclass
class ForwardNode(ASTNode):
    distance: ASTNode

@dataclass
class BackwardNode(ASTNode): 
    distance: ASTNode

@dataclass
class LeftNode(ASTNode):
    angle: ASTNode

@dataclass
class RightNode(ASTNode): 
    angle: ASTNode

@dataclass
class RepeatNode(ASTNode):
    times: ASTNode
    body: list[ASTNode]

@dataclass
class PenUpNode(ASTNode): 
    pass

@dataclass
class PenDownNode(ASTNode): 
    pass

@dataclass
class ColorNode(ASTNode): 
    color_name: ASTNode

@dataclass
class WidthNode(ASTNode): 
    size: ASTNode

@dataclass
class SpeedNode(ASTNode): 
    level: ASTNode

##########################################
#   PARSER (Recursive Descent)
##########################################

class Parser:
    """
    Recursive Descent Parser for the Carapace DSL.
    Converts a stream of tokens into an Abstract Syntax Tree (AST).
    """
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0 

    def current_token(self) -> Token:
        """Returns the token at the current parsing position."""
        return self.tokens[self.pos]

    def consume(self, expected_type: TokenType) -> Token:
        """
        Validates the current token type, advances the position, and returns the token.
        Raises ParserError if the type does not match.
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

    def parse(self) -> list[ASTNode]:
        """
        Entry point: Parses the entire token stream until EOF.
        Grammar: <Program> ::= <Statement>* EOF
        """
        statements = []
        while self.current_token().type != TokenType.EOF:
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> ASTNode:
        """
        Determines which type of statement or command to parse.
        Grammar: <Statement> ::= <Command> | <Loop> | <Assignment>
        """
        token = self.current_token()
        match token.type:
            case TokenType.SET:      return self.parse_set()
            case TokenType.FORWARD:  return self.parse_forward()
            case TokenType.BACKWARD: return self.parse_backward()
            case TokenType.LEFT:     return self.parse_left()
            case TokenType.RIGHT:    return self.parse_right()
            case TokenType.REPEAT:   return self.parse_repeat()
            case TokenType.COLOR:    return self.parse_color()
            case TokenType.WIDTH:    return self.parse_width()
            case TokenType.SPEED:    return self.parse_speed()
            case TokenType.PENUP:
                self.consume(TokenType.PENUP)
                return PenUpNode()
            case TokenType.PENDOWN:
                self.consume(TokenType.PENDOWN)
                return PenDownNode()
            case _:
                raise ParserError(f"Line {token.line}: Unexpected token {token.type.name}")

    def parse_expression(self) -> ASTNode:
        """
        Parses an operand: a numeric literal, a string literal, or a variable identifier.
        Grammar: <Expression> ::= NUMBER | STRING | IDENTIFIER
        """
        token = self.current_token()
        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER)
            return LiteralNode(token.value)
        elif token.type == TokenType.STRING:
            self.consume(TokenType.STRING)
            return LiteralNode(token.value)
        elif token.type == TokenType.IDENTIFIER:
            self.consume(TokenType.IDENTIFIER)
            return VariableNode(name=token.value)
        else:
            raise ParserError(f"Line {token.line}: Expected Number, String or Identifier, but got {token.type.name}")

    def parse_set(self) -> ASTNode:
        """Parses variable assignment: SET <name> <value>."""
        self.consume(TokenType.SET)
        name_token = self.consume(TokenType.IDENTIFIER)
        value_node = self.parse_expression()
        return SetNode(name=name_token.value, value=value_node)

    def parse_forward(self) -> ASTNode:
        """Parses FORWARD command followed by an expression."""
        self.consume(TokenType.FORWARD)
        return ForwardNode(distance=self.parse_expression())

    def parse_backward(self) -> ASTNode:
        """Parses BACKWARD command followed by an expression."""
        self.consume(TokenType.BACKWARD)
        return BackwardNode(distance=self.parse_expression())

    def parse_left(self) -> ASTNode:
        """Parses LEFT command followed by an angle expression."""
        self.consume(TokenType.LEFT)
        return LeftNode(angle=self.parse_expression())

    def parse_right(self) -> ASTNode:
        """Parses RIGHT command followed by an angle expression."""
        self.consume(TokenType.RIGHT)
        return RightNode(angle=self.parse_expression())

    def parse_color(self) -> ASTNode:
        """Parses COLOR command followed by a string or variable."""
        self.consume(TokenType.COLOR)
        return ColorNode(color_name=self.parse_expression())

    def parse_width(self) -> ASTNode:
        """Parses WIDTH command followed by an expression."""
        self.consume(TokenType.WIDTH)
        return WidthNode(size=self.parse_expression())

    def parse_speed(self) -> ASTNode:
        """Parses SPEED command followed by an expression."""
        self.consume(TokenType.SPEED)
        return SpeedNode(level=self.parse_expression())

    def parse_repeat(self) -> ASTNode:
        """
        Parses a REPEAT loop. 
        Grammar: REPEAT <expression> "[" <statement>* "]"
        """
        self.consume(TokenType.REPEAT)
        times_expr = self.parse_expression()
        self.consume(TokenType.LBRACKET)

        body = []
        while self.current_token().type != TokenType.RBRACKET:
            if self.current_token().type == TokenType.EOF:
                raise ParserError("Unclosed REPEAT block: missing ']'")
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACKET)
        return RepeatNode(times=times_expr, body=body) 