from src.lexer import TokenType
from src.parser import BinOpNode, LiteralNode, VariableNode
from src.interpreter import Interpreter


def test_interpreter_evaluates_basic_expression():
    interpreter = Interpreter([])
    interpreter.env.set("x", 7)

    expr = BinOpNode(VariableNode("x"), TokenType.PLUS, LiteralNode(5))

    assert interpreter.evaluate(expr) == 12


def test_interpreter_reads_variable_value():
    interpreter = Interpreter([])
    interpreter.env.set("radius", 12)

    assert interpreter.evaluate(VariableNode("radius")) == 12
