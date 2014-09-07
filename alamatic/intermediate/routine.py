
class Routine(object):
    """
    Represents a routine of executable code.

    This is an abstract type. The subclasses :py:class:`Function`,
    :py:class:`Task` and :py:class:`Module` represent two different kinds of
    routines.

    A routine is the combination of a control flow graph (representing the
    code for the routine), and its local symbols (representing the structure of
    the routine's local storage).
    """

    def __init__(self, graph, symbols):
        self.graph = graph
        self.symbols = symbols

    @property
    def imported_modules(self):
        """
        Iterable of modules directly imported by this routine.
        """
        # TODO: Implement this
        if False:
            yield None

    @property
    def called_functions(self):
        """
        Iterable of functions directly called by this routine.
        """
        # TODO: Implement this
        if False:
            yield None


class Function(Routine):
    """
    Represents a callable function.

    Functions are called from tasks or from other functions and they take
    parameters and optionally return a value.

    Functions cannot yield and as such retain exclusive control until they
    complete, except for interrupt handling.

    The local symbols for a function are allocated on the stack and are
    thus alive for as long as the related stack frame.
    """

    def __init__(self, graph, params, symbols):
        super(Routine, self).__init__(graph, symbols)
        self.params = params


class Task(Routine):
    """
    Represents a task (a coroutine).

    Tasks are allocated -- most commonly as static globals -- and act as
    cooperatively-scheduled stackless threads that retain exclusive control
    (except interrupt handling) except at language constructs that yield,
    at which point other routines get an opportunity to run.

    The local symbols for a task are allocated as a structure stored as part
    of the variable containing the task. Thus the lifetime of the task's data
    is the lifetime of that variable.

    Every program has at least one task, which is known as the "entry task".
    This task is the first to be scheduled after module initialization code
    has completed. Other tasks can be started by the entry task, and they
    may execute if the entry task yields.
    """
    pass


class Module(Routine):
    """
    Represents the construction code for a module.

    The local symbols for a module become globals in the resulting program,
    and any code remaining after preprocessing represents the initialization
    code for the module, which will be executed before that of all dependent
    modules and before the program's entry task is scheduled.
    """
    pass
