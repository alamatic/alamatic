
class PreprocessorError(CompilerError):

    def __init__(self, frame=None, *args, **kwargs):
        self.frame = frame
        # TODO: implement additional_info_items to produce a stack
        # trace for preprocessor errors.


class SymbolNotInitializedError(PreprocessorError):
    pass


class InappropriateTypeError(PreprocessorError):
    pass


class SymbolValueNotKnownError(PreprocessorError):
    pass
