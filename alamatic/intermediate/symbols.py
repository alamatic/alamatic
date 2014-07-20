

class Symbol(object):
    def __init__(
        self,
        decl_table,
        decl_source_range=None,
    ):
        self.decl_table = decl_table
        self.decl_source_range = decl_source_range
        self.type = None
        self.init_source_range = None

    def make_operand(self, source_range=None):
        from alamatic.intermediate.operands import SymbolOperand
        return SymbolOperand(
            self,
            source_range=source_range,
        )

    @property
    def assignable(self):
        return False

    def __repr__(self):
        return '<alamatic.intermediate.%s %s>' % (
            type(self).__name__,
            str(self),
        )


class NamedSymbol(Symbol):

    def __init__(
        self,
        decl_table,
        decl_name,
        const=False,
        decl_source_range=None
    ):
        super(NamedSymbol, self).__init__(
            decl_table, decl_source_range=decl_source_range,
        )
        self.decl_name = decl_name
        self.const = const

    def initialize(self, type_, const=False, source_range=None):
        if self.type is None:
            self.type = type_
            self.const = const
            self.init_source_range = source_range
        else:
            # Should never happen
            raise Exception(
                "Symbol already initialized"
            )

    @property
    def assignable(self):
        return not self.const

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    @property
    def user_friendly_name(self):
        return self.decl_name

    def __str__(self):
        return '%s from %r' % (
            self.decl_name,
            self.decl_source_range,
        )


class TemporarySymbol(Symbol):

    def __init__(
        self,
        decl_table,
        index=None,
    ):
        super(TemporarySymbol, self).__init__(
            decl_table, decl_source_range=None,
        )
        self.index = index

    @property
    def codegen_name(self):
        return "_tmp_%x" % id(self)

    @property
    def user_friendly_name(self):
        # temporaries should never end up being presented to the user,
        # but if there's a bug then returning something nice here may
        # help debug it.
        return "temporary %x" % (self.index, id(self))

    def __str__(self):
        return 'temp(%x)' % (
            id(self),
        )
