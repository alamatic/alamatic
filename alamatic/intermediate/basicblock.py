
class BasicBlock(object):

    def __init__(self, graph):
        self.graph = graph
        self.body_instrs = []
        self.terminator = None
