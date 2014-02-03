"""
The preprocessor is responsible for taking an unannotated Unit
and performing pre-processing operations on it to prepare it for code
generation. After pre-processing:

 * All of the symbols will have a known type and the types are guaranteed to
   be correct and consistent.

 * The values of constants will be "flattened" into the program.

 * All calls will be resolved into either direct calls to other units or to
   indirect calls via instances of the FuncRef type.

If the above cannot be guaranteed for a given unit then an error will be raised
during preprocessing that indicates an error in the program.

The preprocessor catches many kinds of errors as part of its work, but it
does not guarantee that the program has been reduced enough for successful
code generation, so the code generator still has some work to do to validate
the outcome of this phase.
"""

from alamatic.preprocessor.errors import *
from alamatic.preprocessor.execute import *
from alamatic.preprocessor.datastate import *
from alamatic.preprocessor.program import *

