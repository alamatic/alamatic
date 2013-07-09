
class AstNode(object):
    position = None

    def __init__(self, position):
        self.position = position


class Module(AstNode):

    def __init__(self, position, name, stmts):
        self.name = name
        self.stmts = stmts
        self.position = position


class Statement(AstNode):
    pass


class Expression(AstNode):
    pass


class PassStatement(Statement):
    pass
