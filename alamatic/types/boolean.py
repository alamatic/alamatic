
from alamatic.types.base import *
from alamatic.compilelogging import pos_link


class Bool(Value):
    def __init__(self, value):
        if type(value) is not bool:
            raise Exception(
                "Value %r is not boolean" % value
            )

        self.value = value

    def __repr__(self):
        return "<alamatic.types.%s: %r>" % (type(self).__name__, self.value)

    def generate_c_code(self, state, writer):
        writer.write("1" if self.value else "0")

    @classmethod
    def c_type_spec(self):
        return "_Bool"
