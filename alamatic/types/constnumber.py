
from alamatic.types.base import Type
import llvm.core
import numbers


__all__ = ['ConstNumber']


class ConstNumberType(Type):
    """
    Compile-time-only type that is the type of numeric constants in source.

    This type can represent numbers far larger (or, for floating point,
    more precise) than the runtime-supported numeric types.

    It uses a base-10 exponent for floating point because fractional literals
    are written in decimal notation and thus we can accurately store all
    reasonable-sized real numbers as written in the source.

    Conversion to the "float" and "double" types will cause approximation
    for any value that cannot be represented with a base 2 exponent.
    """

    significand_llvm_type = llvm.core.Type.int(128)
    exponent_llvm_type = llvm.core.Type.int(16)

    component_llvm_type = llvm.core.Type.struct([
        significand_llvm_type,
        exponent_llvm_type,
    ]),

    llvm_type = llvm.core.Type.struct([
        component_llvm_type[0],  # real part
        component_llvm_type[0],  # imaginary part
    ])

    def make_constant_data(self, parts):
        return llvm.core.Constant.struct(
            [
                llvm.core.Constant.struct(
                    [
                        llvm.core.Constant.int(
                            self.significand_llvm_type,
                            parts.real.significand,
                        ),
                        llvm.core.Constant.int(
                            self.significand_llvm_type,
                            parts.real.exponent,
                        ),
                    ]
                ),
                llvm.core.Constant.struct(
                    [
                        llvm.core.Constant.int(
                            self.significand_llvm_type,
                            parts.imaginary.significand,
                        ),
                        llvm.core.Constant.int(
                            self.significand_llvm_type,
                            parts.imaginary.exponent,
                        ),
                    ]
                ),
            ]
        )

    def repr_for_data(self, data):
        index_type = llvm.core.Type.int(1)

        real_str = format_component(
            data.extract_element(
                llvm.core.Constant.int(index_type, 0),
            )
        )
        imag_str = format_component(
            data.extract_element(
                llvm.core.Constant.int(index_type, 1),
            )
        )

        if imag_str == "0":
            imag_str = ""
        else:
            imag_str += "j"

        if real_str == "0" and imag_str != "":
            real_str = ""

        if real_str != "" and imag_str != "":
            real_str = "(" + real_str
            imag_str = "+" + imag_str + ")"

        return real_str + imag_str


def format_component(data):
    # This is pretty circuitous but it will do for now since we
    # only use this for debugging
    from decimal import Decimal

    index_type = llvm.core.Type.int(1)
    significand = data.extract_element(
        llvm.core.Constant.int(index_type, 0),
    ).s_ext_value
    exponent = data.extract_element(
        llvm.core.Constant.int(index_type, 1),
    ).s_ext_value

    sign = 0 if significand >= 0 else 1
    digits = tuple(int(x) for x in str(abs(significand)))
    parts = (sign, digits, exponent)
    decimal = Decimal(parts)
    return str(decimal)


ConstNumber = ConstNumberType()
