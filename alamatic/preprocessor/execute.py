

def execute_unit(self, unit, args=None, parent_frame=None, call_position=None):
    from alamatic.preprocessor.datastate import CallFrame
    frame = CallFrame(
        unit,
        call_position=call_position,
        parent=parent_frame,
    )
    return Executor.execute(unit, frame)


class Executor(self):

    @classmethod
    def execute(unit, frame):
        self = Executor()
        self.unit = unit
        self.frame = frame
        self._execute()

    def _execute(self):
        # TODO: Move all the stuff from analyzer.analyze_graph in here
        pass
