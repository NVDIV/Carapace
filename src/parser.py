from dataclasses import dataclass

##########################################
#   AST NODES (Узлы дерева)
##########################################
# Базовый класс для любой команды (узла)
class ASTNode:
    pass

@dataclass
class ForwardNode(ASTNode):
    distance: int  # Сколько шагов пройти

@dataclass
class PenUpNode(ASTNode):
    pass # У этой команды нет аргументов

##########################################
#   PARSER
##########################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0 # Текущий токен, на который смотрим

    def parse(self):
        # TODO: Проходить по списку токенов.
        # TODO: Если видим токен FORWARD -> проверить, что следующий токен NUMBER.
        # TODO: Если да, создать ForwardNode(значение_числа) и добавить в список (дерево).
        # TODO: Вернуть список готовых AST узлов.
        pass