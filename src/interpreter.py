from src.parser import ASTNode, ForwardNode, LeftNode, RepeatNode, BackwardNode, RightNode, PenUpNode, PenDownNode, ColorNode, WidthNode, SpeedNode
import src.commands as commands
from src.errors import RuntimeError

##########################################
#   INTERPRETER
##########################################

class Interpreter:
    def __init__(self, tree: list[ASTNode]):
        self.tree = tree

    def run(self):
        """Main execution method. Traverses the AST root nodes."""
        commands.init_graphics()
        
        # Iterate over the root nodes of our tree
        for node in self.tree:
            self.execute(node)
            
        commands.finish_graphics()

    def execute(self, node: ASTNode):
        """Executes a single AST node based on its type."""
        
        match node:
            case ForwardNode(distance=d):
                commands.execute_forward(d)

            case BackwardNode(d): 
                commands.execute_backward(d)

            case LeftNode(angle=a):
                commands.execute_left(a)

            case RightNode(a): 
                commands.execute_right(a)

            case RepeatNode(times=t, body=b):
                # Loop logic: repeat 't' times
                for _ in range(t):
                    # Recursively execute each child node in the loop body
                    for child_node in b:
                        self.execute(child_node)

            case PenUpNode(): 
                commands.execute_penup()

            case PenDownNode(): 
                commands.execute_pendown()

            case ColorNode(c): 
                commands.execute_color(c)

            case WidthNode(w): 
                commands.execute_width(w)

            case SpeedNode(s): 
                commands.execute_speed(s)

            case _:
                raise RuntimeError(f"Unknown AST node: {node}")