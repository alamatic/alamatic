
import alamatic.diagnostics as diag


class Initialization(object):

    def __init__(self, value, source_range=None):
        self.value = value
        self.source_range = source_range


class AnalysisResult(object):

    def __init__(
        self,
        function,
        global_inits,
        constant_inits
    ):
        self.function = function
        self.global_inits = global_inits
        self.local_inits = [None for x in function.local_variables]
        self.diagnostics = []
        self.constant_inits = constant_inits
        self.register_inits = [None] * function.register_count

    @classmethod
    def merge(cls, results):
        if len(results) == 0:
            raise Exception("Can't merge empty set of analysis results")

        from alamatic.types import Poison

        function = results[0].function
        global_types = []
        constant_values = []
        self = cls(function, global_types, constant_values)

        diagnostics = self.diagnostics
        for result in results:
            diagnostics.extend(result.diagnostics)

        for result in results:
            for idx, init in enumerate(result.register_inits):
                if self.register_inits[idx] is not None:
                    # This should never happen as long as the AST lowering
                    # is behaving itself.
                    raise Exception(
                        "Multiple initializations for register %03x" % idx
                    )

                if result.register_inits[idx] is not None:
                    self.register_inits[idx] = result.register_inits[idx]

            for idx, init in enumerate(result.constant_inits):
                if self.constant_inits[idx] is None:
                    self.constant_inits[idx] = init
                else:
                    if self.constant_inits[idx].value is Poison:
                        continue

                    previous_init = self.constant_inits[idx]
                    self.add_diagnostic(
                        diag.ConstantMultipleInitialization(
                            # TODO: Figure out how to get at the symbol
                            # name in here.
                            symbol_name='TODO',
                            init_1_range=previous_init.source_range,
                            init_2_range=init.source_range,
                        )
                    )

                    self.constant_inits[idx] = Initialization(Poison)

            for idx, init in enumerate(result.global_inits):
                if self.global_inits[idx] is not None:
                    previous_type = self.global_inits[idx].value.type
                    new_type = init.value.type

                    if previous_type is not new_type:
                        self.add_diagnostic(
                            diag.SymbolTypeMismatch(
                                # TODO: Figure out how to get at the symbol
                                # name in here.
                                symbol_name='TODO',
                                type_1=previous_type,
                                type_1_range=(
                                    self.global_inits[idx].source_range
                                ),
                                type_2=new_type,
                                type_2_range=(
                                    init.source_range
                                ),
                            )
                        )
                        self.global_inits[idx] = Initialization(Poison)
                        continue
                    else:
                        # We'll just arbitrarily keep the earlier
                        # initialization, which will usually be from
                        # earlier in the source code.
                        continue
                else:
                    self.global_inits[idx] = init

    def add_diagnostic(self, diagnostic):
        self.diagnostics.append(diagnostic)
