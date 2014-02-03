

class Unit(object):
    """
    A single unit of execution.

    Most often this is a function but it can also be the initialization code
    for a module, which gets compiled as a function that takes no parameters.
    """

    def __init__(self, graph, symbols, params):
        self.graph = graph
        self.symbols = symbols
        self.params = params
