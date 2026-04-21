from src.lexer import TokenType
from src.parser import (
    ASTNode, ForwardNode, IfNode, LeftNode, RepeatNode, BackwardNode, 
    RightNode, PenUpNode, PenDownNode, ColorNode, WidthNode, 
    SpeedNode, SetNode, LiteralNode, VariableNode, BinOpNode
)
import src.commands as commands
from src.errors import RuntimeError

class Environment:
    """
    Stores variable names and their corresponding values.
    """
    def __init__(self):
        self.variables = {}

    def set(self, name: str, value: any):
        """Define or update a variable value."""
        self.variables[name] = value

    def get(self, name: str):
        """Retrieve a variable value or raise an error if undefined."""
        if name in self.variables:
            return self.variables[name]
        raise RuntimeError(f"Undefined variable: '{name}'")

class Interpreter:
    """
    Executes the Abstract Syntax Tree (AST) by mapping nodes to turtle commands.
    """
    def __init__(self, tree: list[ASTNode]):
        self.tree = tree
        self.env = Environment()

    def run(self):
        """Main execution loop. Initializes graphics and traverses root nodes."""
        commands.init_graphics()
        try:
            for node in self.tree:
                self.execute(node)
        finally:
            # Ensures graphics window stays open or closes properly even on error
            commands.finish_graphics()

    def evaluate(self, node: ASTNode) -> any:
            match node:
                case LiteralNode(value=v):
                    return v
                case VariableNode(name=n):
                    return self.env.get(n)
                case BinOpNode(left=l, op=op, right=r):
                    left_val = self.evaluate(l)
                    right_val = self.evaluate(r)
                    
                    # Perform the operation based on the token type
                    if op == TokenType.PLUS: return left_val + right_val
                    if op == TokenType.MINUS: return left_val - right_val
                    if op == TokenType.MULTIPLY: return left_val * right_val
                    if op == TokenType.DIVIDE: return left_val / right_val
                    
                    raise RuntimeError(f"Unknown operator: {op}")
                case _:
                    return node

    def execute(self, node: ASTNode):
        """Executes a single AST node by resolving expressions and calling commands."""
        match node:
            case SetNode(name=n, value=v):
                # Resolve the expression and save it to the environment
                val = self.evaluate(v)
                self.env.set(n, val)

            case ForwardNode(distance=d):
                val = self.evaluate(d)
                commands.execute_forward(val)

            case BackwardNode(distance=d): 
                val = self.evaluate(d)
                commands.execute_backward(val)

            case LeftNode(angle=a):
                val = self.evaluate(a)
                commands.execute_left(val)

            case RightNode(angle=a): 
                val = self.evaluate(a)
                commands.execute_right(val)

            case RepeatNode(times=t, body=b):
                # Resolve how many times to loop
                count = int(self.evaluate(t))
                for _ in range(count):
                    for child_node in b:
                        self.execute(child_node)

            case IfNode(left, op, right, body):
                l_val = self.evaluate(left)
                r_val = self.evaluate(right)
                
                condition = False
                if op == TokenType.EQ: condition = (l_val == r_val)
                elif op == TokenType.LT: condition = (l_val < r_val)
                elif op == TokenType.GT: condition = (l_val > r_val)
                
                if condition:
                    for child in body:
                        self.execute(child)

            case ColorNode(color_name=c): 
                val = self.evaluate(c)
                commands.execute_color(val)

            case WidthNode(size=w): 
                val = self.evaluate(w)
                commands.execute_width(val)

            case SpeedNode(level=s): 
                val = self.evaluate(s)
                commands.execute_speed(val)

            case PenUpNode(): 
                commands.execute_penup()

            case PenDownNode(): 
                commands.execute_pendown()

            case _:
                raise RuntimeError(f"Unknown AST node type: {type(node).__name__}")