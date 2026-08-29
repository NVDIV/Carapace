from src.lexer import TokenType
from src.parser import (
    ASTNode, ForwardNode, IfNode, LeftNode, RepeatNode, BackwardNode, 
    RightNode, PenUpNode, PenDownNode, ColorNode, WidthNode, 
    SpeedNode, SetNode, LiteralNode, VariableNode, BinOpNode, FunctionDefNode, FunctionCallNode, ReturnNode
)
import src.commands as commands
from src.errors import RuntimeError, ReturnSignal

class Environment:
    """
    Stores variable names and their corresponding values.
    """
    def __init__(self, parent=None):
        self.variables = {}
        self.functions = {}  # Funkcje zazwyczaj zostawiamy globalne lub w zasięgu leksykalnym
        self.parent = parent

    def set(self, name: str, value: any):
        """Definiuje zmienną w BIEŻĄCYM zasięgu (zawsze lokalnie)."""
        self.variables[name] = value

    def get(self, name: str):
        """Szuka zmiennej w bieżącym zasięgu, a jeśli nie znajdzie - u rodzica."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable: '{name}'")

    def define_function(self, node: FunctionDefNode):
        # Zapisujemy cały węzeł, bo on ma w sobie i nazwę, i parametry, i body
        self.functions[node.name] = node

    def get_function(self, name: str) -> FunctionDefNode:
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        raise RuntimeError(f"Undefined function: '{name}'")
    
class Interpreter:
    """
    Executes the Abstract Syntax Tree (AST) by mapping nodes to turtle commands.
    """
    def __init__(self, tree: list[ASTNode]):
        self.tree = tree
        # Tworzymy środowisko globalne
        self.global_env = Environment()
        # env to nasze "bieżące" środowisko (na początku globalne)
        self.env = self.global_env

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
                case FunctionCallNode(name=n, args=args):
                    # Funkcja wywołana jako część wyrażenia! 
                    # Musimy ją "wykonać", aby dostać jej wynik.
                    return self.execute(node) 
            
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

            case FunctionDefNode(name=n, params=p, body=b):
                # Po prostu rejestrujemy cały węzeł w środowisku
                self.env.define_function(node)

            case FunctionCallNode(name=n, args=arguments):
                # 1. Pobierz definicję
                func_node = self.env.get_function(n)
                
                # 2. Oblicz argumenty w bieżącym środowisku (przed zmianą scope'u!)
                evaluated_args = [self.evaluate(arg) for arg in arguments]
                
                # 3. Sprawdź czy liczba argumentów się zgadza
                if len(evaluated_args) != len(func_node.params):
                    raise RuntimeError(f"Function '{n}' expects {len(func_node.params)} args, got {len(evaluated_args)}")

                # 4. TWORZENIE SCOPE: To jest serce problemu.
                # Rodzicem musi być GLOBAL_ENV, aby funkcja miała dostęp do zmiennych globalnych,
                # ale NIE do zmiennych lokalnych innych funkcji wywołanych wcześniej.
                new_scope = Environment(parent=self.global_env)
                
                # 5. Przypisz argumenty do nazw parametrów
                for param_name, value in zip(func_node.params, evaluated_args):
                    new_scope.set(param_name, value)
                
                # 6. Wykonaj w nowym środowisku
                previous_env = self.env
                self.env = new_scope
                
                try:
                    for child in func_node.body:
                        self.execute(child)
                except ReturnSignal as ret:
                    return ret.value
                finally:
                    # 7. ZAWSZE wracaj do poprzedniego środowiska
                    self.env = previous_env
                return None


            case ReturnNode(value=v):
                val = self.evaluate(v)
                raise ReturnSignal(val)
                    