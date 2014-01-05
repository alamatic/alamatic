
class Element(object):
    position = None

    def __init__(self, position=None):
        self.position = position

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (', '.join(
            (str(x) for x in self.params)
        )) + " : " + repr(self.position) + ")"

    def __repr__(self):
        return "<alamatic.intermediate.%s>" % self.__str__()

    def generate_c_code(self, state, writer):
        raise Exception(
            "generate_c_code not implemented for %r" % self
        )


class Label(Element):

    def generate_c_code(self, state, writer):
        writer.writeln("%s:" % self.codegen_name)

    @property
    def codegen_name(self):
        return "_ALA_%x" % id(self)

    def replace_operands(self, replace):
        pass
