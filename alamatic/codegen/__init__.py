
from alamatic.codegen.codewriter import CodeWriter
from alamatic.codegen.cbackend import (
    CBackend,
)


def generate_c_code(program, stream):
    writer = CodeWriter(stream)
    CBackend.generate_code(program, writer)
