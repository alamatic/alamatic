
import threading
import contextlib


__all__ = [
    "context",
    "new_context",
]

context = threading.local()
context.symbol_types = None
context.symbol_constant_values = None
context.symbol_llvm_values = None


@contextlib.contextmanager
def new_context(
    symbol_types=None,
    symbol_constant_values=None,
    symbol_llvm_values=None,
):
    old_symbol_types = context.symbol_types
    old_symbol_constant_values = context.symbol_constant_values
    old_symbol_llvm_values = context.symbol_llvm_values

    if symbol_types is not None:
        context.symbol_types = symbol_types

    if symbol_constant_values is not None:
        context.symbol_constant_values = symbol_constant_values

    if symbol_llvm_values is not None:
        context.symbol_llvm_values = symbol_llvm_values

    try:
        yield
    finally:
        context.symbol_types = old_symbol_types
        context.symbol_constant_values = old_symbol_constant_values
        context.symbol_llvm_values = old_symbol_llvm_values
