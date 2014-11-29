
from alamatic.types.base import *
from alamatic.types.integer import *
from alamatic.types.constnumber import *


__all__ = ["intrinsic_types"]


intrinsic_types = {
    "Int64": Int64,
    "UInt64": UInt64,
    "Int32": Int32,
    "UInt32": UInt32,
    "Int16": Int16,
    "UInt16": UInt16,
    "Int8": Int8,
    "UInt8": UInt8,
    "ConstNumber": ConstNumber,
}


for name, obj in intrinsic_types.iteritems():
    obj.name = name
