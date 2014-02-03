
from alamatic.compilelogging import CompilerError


__all__ = [
    "PreprocessorError",
    "SymbolNotInitializedError",
    "InappropriateTypeError",
    "SymbolValueNotKnownError",
]


class PreprocessorError(CompilerError):

    def __init__(self, *args, **kwargs):
        if "frame" in kwargs:
            self.frame = kwargs["frame"]
            del kwargs["frame"]
        CompilerError.__init__(self, *args, **kwargs)

    # TODO: implement additional_info_items to produce a stack
    # trace for preprocessor errors.


class SymbolNotInitializedError(PreprocessorError):
    pass


class InappropriateTypeError(PreprocessorError):
    pass


class SymbolValueNotKnownError(PreprocessorError):
    pass
