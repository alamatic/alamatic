
class AstNode(object):
    position = None


class Module(AstNode):

    def __init__(self, position, name, stmts):
        self.name = name
        self.stmts = stmts
        self.position = position


class Statement(AstNode):
    pass


class Expression(AstNode):
    pass
