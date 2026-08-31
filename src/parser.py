"""Recursive-descent parser for the Carapace language.

The parser consumes lexer tokens and produces an Abstract Syntax Tree (AST).
It is responsible only for syntactic structure; semantic validity is checked
later by :mod:`src.semantic_analyzer`.
"""

from Carapace.src.lexer import TokenType, Token
from Carapace.src.errors import ParserError
import Carapace.src.ast as ast_nodes


class Parser:
    """Convert a Carapace token stream into an Abstract Syntax Tree."""

    def __init__(self, tokens: list[Token]):
        """Initialize parser state over a complete token sequence."""
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        """Return the token at the current parsing position."""
        return self.tokens[self.pos]

    def consume(self, expected_type: TokenType) -> Token:
        """Consume one token of ``expected_type`` or raise ``ParserError``."""
        token = self.current_token()
        if token.type == expected_type:
            self.pos += 1
            return token
        else:
            raise ParserError(
                f"Line {token.line}: Expected {expected_type.name}, "
                f"but got {token.type.name} ('{token.value}')"
            )

    def parse(self) -> list[ast_nodes.ASTNode]:
        """Parse the complete token stream according to ``Program`` grammar."""
        statements = []
        while self.current_token().type != TokenType.EOF:
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> ast_nodes.ASTNode:
        """Dispatch the current token to the matching statement parser."""
        token = self.current_token()

        match token.type:
            case TokenType.SET:
                return self.parse_set()
            case TokenType.FORWARD:
                return self.parse_forward()
            case TokenType.BACKWARD:
                return self.parse_backward()
            case TokenType.LEFT:
                return self.parse_left()
            case TokenType.RIGHT:
                return self.parse_right()
            case TokenType.REPEAT:
                return self.parse_repeat()
            case TokenType.IF:
                return self.parse_if()
            case TokenType.COLOR:
                return self.parse_color()
            case TokenType.WIDTH:
                return self.parse_width()
            case TokenType.SPEED:
                return self.parse_speed()
            case TokenType.FUNC:
                return self.parse_function()
            case TokenType.CALL:
                return self.parse_call()
            case TokenType.RETURN:
                return self.parse_return()
            case TokenType.PENUP:
                command_token = self.consume(TokenType.PENUP)
                return ast_nodes.PenUpNode(line=command_token.line)
            case TokenType.PENDOWN:
                command_token = self.consume(TokenType.PENDOWN)
                return ast_nodes.PenDownNode(line=command_token.line)
            case _:
                raise ParserError(
                    f"Line {token.line}: Unexpected token {token.type.name}"
                )

    # ===================================================================
    # Expressions
    # ===================================================================

    def parse_expression(self) -> ast_nodes.ASTNode:
        """Parse addition and subtraction, the lowest-precedence operators."""
        node = self.parse_term()

        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.consume(self.current_token().type)
            node = ast_nodes.BinOpNode(
                left=node,
                op=op_token.type,
                right=self.parse_term(),
                line=op_token.line,
            )

        return node

    def parse_term(self) -> ast_nodes.ASTNode:
        """Parse multiplication and division before additive operators."""
        node = self.parse_factor()

        while self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op_token = self.consume(self.current_token().type)
            node = ast_nodes.BinOpNode(
                left=node,
                op=op_token.type,
                right=self.parse_factor(),
                line=op_token.line,
            )

        return node

    def parse_factor(self) -> ast_nodes.ASTNode:
        """Parse literals, variables, parenthesized expressions and calls."""
        token = self.current_token()

        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER)
            return ast_nodes.LiteralNode(token.value, line=token.line)
        elif token.type == TokenType.STRING:
            self.consume(TokenType.STRING)
            return ast_nodes.LiteralNode(token.value, line=token.line)
        elif token.type == TokenType.IDENTIFIER:
            self.consume(TokenType.IDENTIFIER)
            return ast_nodes.VariableNode(name=token.value, line=token.line)
        elif token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            node = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return node
        elif token.type == TokenType.CALL:
            return self.parse_call()
        else:
            raise ParserError(
                f"Line {token.line}: Unexpected token {token.type.name} in expression"
            )

    # ===================================================================
    # Simple statements and drawing commands
    # ===================================================================

    def parse_set(self) -> ast_nodes.ASTNode:
        """Parse ``SET <name> <expression>``."""
        command_token = self.consume(TokenType.SET)
        name_token = self.consume(TokenType.IDENTIFIER)
        value_node = self.parse_expression()
        return ast_nodes.SetNode(
            name=name_token.value,
            value=value_node,
            line=command_token.line,
        )

    def parse_forward(self) -> ast_nodes.ASTNode:
        """Parse a ``FORWARD`` command and its distance expression."""
        command_token = self.consume(TokenType.FORWARD)
        return ast_nodes.ForwardNode(
            distance=self.parse_expression(),
            line=command_token.line,
        )

    def parse_backward(self) -> ast_nodes.ASTNode:
        """Parse a ``BACKWARD`` command and its distance expression."""
        command_token = self.consume(TokenType.BACKWARD)
        return ast_nodes.BackwardNode(
            distance=self.parse_expression(),
            line=command_token.line,
        )

    def parse_left(self) -> ast_nodes.ASTNode:
        """Parse a ``LEFT`` command and its angle expression."""
        command_token = self.consume(TokenType.LEFT)
        return ast_nodes.LeftNode(
            angle=self.parse_expression(),
            line=command_token.line,
        )

    def parse_right(self) -> ast_nodes.ASTNode:
        """Parse a ``RIGHT`` command and its angle expression."""
        command_token = self.consume(TokenType.RIGHT)
        return ast_nodes.RightNode(
            angle=self.parse_expression(),
            line=command_token.line,
        )

    def parse_color(self) -> ast_nodes.ASTNode:
        """Parse a ``COLOR`` command and its value expression."""
        command_token = self.consume(TokenType.COLOR)
        return ast_nodes.ColorNode(
            color_name=self.parse_expression(),
            line=command_token.line,
        )

    def parse_width(self) -> ast_nodes.ASTNode:
        """Parse a ``WIDTH`` command and its value expression."""
        command_token = self.consume(TokenType.WIDTH)
        return ast_nodes.WidthNode(
            size=self.parse_expression(),
            line=command_token.line,
        )

    def parse_speed(self) -> ast_nodes.ASTNode:
        """Parse a ``SPEED`` command and its value expression."""
        command_token = self.consume(TokenType.SPEED)
        return ast_nodes.SpeedNode(
            level=self.parse_expression(),
            line=command_token.line,
        )

    # ===================================================================
    # Control flow
    # ===================================================================

    def parse_repeat(self) -> ast_nodes.ASTNode:
        """Parse ``REPEAT <expression> [ <statement>* ]``."""
        command_token = self.consume(TokenType.REPEAT)
        times_expr = self.parse_expression()
        self.consume(TokenType.LBRACKET)

        body = []
        while self.current_token().type != TokenType.RBRACKET:
            if self.current_token().type == TokenType.EOF:
                raise ParserError(
                    f"Line {command_token.line}: Unclosed REPEAT block: missing ']'"
                )
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACKET)
        return ast_nodes.RepeatNode(
            times=times_expr,
            body=body,
            line=command_token.line,
        )

    def parse_if(self) -> ast_nodes.ASTNode:
        """Parse ``IF <expr> <comparison> <expr> [ <statement>* ]``."""
        command_token = self.consume(TokenType.IF)
        left = self.parse_expression()
        op_type = self.current_token().type

        if op_type not in (TokenType.EQ, TokenType.LT, TokenType.GT):
            raise ParserError(
                f"Line {self.current_token().line}: Expected ==, <, or >, "
                f"but got {op_type.name}"
            )
        self.consume(op_type)

        right = self.parse_expression()
        self.consume(TokenType.LBRACKET)

        body = []
        while self.current_token().type != TokenType.RBRACKET:
            if self.current_token().type == TokenType.EOF:
                raise ParserError(
                    f"Line {command_token.line}: Unclosed IF block: missing ']'"
                )
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACKET)
        return ast_nodes.IfNode(
            left=left,
            op=op_type,
            right=right,
            body=body,
            line=command_token.line,
        )

    # ===================================================================
    # Functions
    # ===================================================================

    def parse_function(self) -> ast_nodes.ASTNode:
        """Parse a global function declaration and its parameter list."""
        command_token = self.consume(TokenType.FUNC)
        name = self.consume(TokenType.IDENTIFIER).value

        params = []
        while self.current_token().type == TokenType.IDENTIFIER:
            params.append(self.consume(TokenType.IDENTIFIER).value)

        self.consume(TokenType.LBRACKET)

        body = []
        while self.current_token().type != TokenType.RBRACKET:
            if self.current_token().type == TokenType.EOF:
                raise ParserError(
                    f"Line {command_token.line}: Unclosed FUNC block: missing ']'"
                )
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACKET)
        return ast_nodes.FunctionDefNode(
            name=name,
            params=params,
            body=body,
            line=command_token.line,
        )

    def parse_call(self) -> ast_nodes.ASTNode:
        """Parse a function call with zero or more greedily parsed arguments."""
        command_token = self.consume(TokenType.CALL)
        name = self.consume(TokenType.IDENTIFIER).value

        args = []
        # Each argument is parsed greedily as a complete expression. A nested
        # call can be made explicit with parentheses: CALL outer (CALL inner 10).
        while self.current_token().type in (
            TokenType.NUMBER,
            TokenType.STRING,
            TokenType.IDENTIFIER,
            TokenType.LPAREN,
        ):
            args.append(self.parse_expression())

        return ast_nodes.FunctionCallNode(
            name=name,
            args=args,
            line=command_token.line,
        )

    def parse_return(self) -> ast_nodes.ASTNode:
        """Parse ``RETURN <expression>``."""
        command_token = self.consume(TokenType.RETURN)
        value = self.parse_expression()
        return ast_nodes.ReturnNode(value=value, line=command_token.line)
