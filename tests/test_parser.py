from src.lexer import Lexer
from src.parser import BinOpNode, LiteralNode, Parser, SetNode


def test_parse_set_statement():
    ast = Parser(Lexer("SET x 10").tokenize()).parse()

    assert len(ast) == 1
    assert isinstance(ast[0], SetNode)
    assert ast[0].name == "x"
    assert isinstance(ast[0].value, LiteralNode)
    assert ast[0].value.value == 10


def test_parse_expression_with_addition():
    ast = Parser(Lexer("SET x 10 + 5").tokenize()).parse()

    node = ast[0]
    assert isinstance(node, SetNode)
    assert isinstance(node.value, BinOpNode)
    assert isinstance(node.value.left, LiteralNode)
    assert node.value.left.value == 10
    assert isinstance(node.value.right, LiteralNode)
    assert node.value.right.value == 5
