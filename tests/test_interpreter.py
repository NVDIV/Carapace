from Carapace.src.lexer import TokenType
from Carapace.src.ast import BinOpNode, LiteralNode, VariableNode
from Carapace.src.interpreter import Interpreter
from Carapace.src.semantic_analyzer import SemanticAnalyzer


def test_interpreter_evaluates_basic_expression():
    """The interpreter evaluates a simple arithmetic AST expression."""
    tree = []
    interpreter = Interpreter(tree, SemanticAnalyzer(tree).analyze())
    interpreter.env.set_variable("x", 7)

    expr = BinOpNode(VariableNode("x"), TokenType.PLUS, LiteralNode(5))

    assert interpreter.evaluate(expr) == 12


def test_interpreter_reads_variable_value():
    """Variable expressions resolve values from the active environment."""
    tree = []
    interpreter = Interpreter(tree, SemanticAnalyzer(tree).analyze())
    interpreter.env.set_variable("radius", 12)

    assert interpreter.evaluate(VariableNode("radius")) == 12
