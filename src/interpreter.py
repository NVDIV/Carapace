from src.parser import ASTNode, ForwardNode, LeftNode, RepeatNode
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

            case LeftNode(angle=a):
                commands.execute_left(a)

            case RepeatNode(times=t, body=b):
                # Loop logic: repeat 't' times
                for _ in range(t):
                    # Recursively execute each child node in the loop body
                    for child_node in b:
                        self.execute(child_node)

            case _:
                raise RuntimeError(f"Unknown AST node: {node}")