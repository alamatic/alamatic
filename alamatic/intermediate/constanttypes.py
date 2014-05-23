
class FunctionTemplate(object):
    """
    A source-level function template that awaits instantiation into a
    "real" function.
    """

    def __init__(self, decl_stmt, decl_scope):
        self.decl_stmt = decl_stmt
        self.decl_scope = decl_scope

    def __repr__(self):
        return "<alamatic.intermediate.FunctionTemplate %s>" % (
            self.decl_stmt.decl.name,
        )
