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
class BinOpNode(ASTNode):
    """Represents binary operation (+, -, *, /)"""
    left: ASTNode
    op: TokenType
    right: ASTNode

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
class IfNode(ASTNode):
    left: ASTNode
    op: TokenType # EQ, LT, GT
    right: ASTNode
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

@dataclass
class FunctionDefNode(ASTNode):
    name: str
    params: list[str]  # Lista nazw params, np. ['size', 'color']
    body: list[ASTNode]

@dataclass
class FunctionCallNode(ASTNode):
    name: str
    args: list[ASTNode] # Lista wyrażeń do obliczenia, np. [LiteralNode(100), VariableNode('x')]

@dataclass
class ReturnNode(ASTNode):
    value: ASTNode  # Wyrażenie, które ma zostać zwrócone

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
            case TokenType.IF:  return self.parse_if()
            case TokenType.COLOR:    return self.parse_color()
            case TokenType.WIDTH:    return self.parse_width()
            case TokenType.SPEED:    return self.parse_speed()
            case TokenType.FUNC: return self.parse_function()
            case TokenType.CALL: return self.parse_call()
            case TokenType.RETURN: return self.parse_return()
            case TokenType.PENUP:
                self.consume(TokenType.PENUP)
                return PenUpNode()
            case TokenType.PENDOWN:
                self.consume(TokenType.PENDOWN)
                return PenDownNode()
            case _:
                raise ParserError(f"Line {token.line}: Unexpected token {token.type.name}")

    def parse_expression(self) -> ASTNode:
        """Handles Addition and Subtraction (Lowest precedence)."""
        node = self.parse_term()
        
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.consume(self.current_token().type).type
            node = BinOpNode(left=node, op=op, right=self.parse_term())
        return node

    def parse_term(self) -> ASTNode:
        """Handles Multiplication and Division (Higher precedence)."""
        node = self.parse_factor()
        
        while self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.consume(self.current_token().type).type
            node = BinOpNode(left=node, op=op, right=self.parse_factor())
        return node

    def parse_factor(self) -> ASTNode:
        """Handles Literals, Variables, and Parentheses (Highest precedence)."""
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
        elif token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            node = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return node
        elif token.type == TokenType.CALL:
            return self.parse_call() # Parser teraz traktuje wywołanie funkcji jako "liczbę"
        else:
            raise ParserError(f"Line {token.line}: Unexpected token {token.type.name} in expression")

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
    
    def parse_if(self) -> ASTNode:
            self.consume(TokenType.IF)

            # Parse the left side as a simple factor or expression
            left = self.parse_expression() 

            # Get the operator
            op_type = self.current_token().type

            # Validate and consume
            if op_type not in (TokenType.EQ, TokenType.LT, TokenType.GT):
                raise ParserError(f"Line {self.current_token().line}: Expected ==, <, or >, but got {op_type.name}")
            self.consume(op_type)

            # Parse the right side
            right = self.parse_expression()
            
            self.consume(TokenType.LBRACKET)
            body = []
            while self.current_token().type != TokenType.RBRACKET:
                if self.current_token().type == TokenType.EOF:
                    raise ParserError("Unclosed IF block: missing ']'")
                body.append(self.parse_statement())
            self.consume(TokenType.RBRACKET)
            
            return IfNode(left=left, op=op_type, right=right, body=body)
    
    def parse_function(self) -> ASTNode:
        self.consume(TokenType.FUNC)
        name = self.consume(TokenType.IDENTIFIER).value
        
        params = []
        # Czytamy parametry tak długo, aż nie napotkamy lewego nawiasu kwadratowego
        while self.current_token().type == TokenType.IDENTIFIER:
            params.append(self.consume(TokenType.IDENTIFIER).value)
        
        self.consume(TokenType.LBRACKET)
        body = []
        while self.current_token().type != TokenType.RBRACKET:
            body.append(self.parse_statement())
        self.consume(TokenType.RBRACKET)
        
        return FunctionDefNode(name=name, params=params, body=body)

    def parse_call(self) -> ASTNode:
        self.consume(TokenType.CALL)
        name = self.consume(TokenType.IDENTIFIER).value
    
        args = []
        # Tutaj mamy wybór: albo czytamy argumenty do końca linii, 
        # albo (bezpieczniej) wymagamy ich w nawiasach lub czytamy określoną liczbę.
        # Na razie czytajmy wyrażenia dopóki się da (uproszczone):
        while self.current_token().type in (TokenType.NUMBER, TokenType.STRING, TokenType.IDENTIFIER, TokenType.LPAREN):
            args.append(self.parse_expression())
            
        return FunctionCallNode(name=name, args=args)

    # Parser method
    def parse_return(self) -> ASTNode:
        self.consume(TokenType.RETURN) # Musisz dodać RETURN do TokenType!
        value = self.parse_expression()
        return ReturnNode(value=value)