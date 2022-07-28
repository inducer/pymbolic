from pymbolic.primitives import Expression
from numbers import Number
from typing import Union

try:
    import numpy as np
except ImportError:
    BoolT = bool
else:
    BoolT = Union[bool, np.bool_]


ScalarT = Union[Number, int, BoolT, float]
ExpressionT = Union[ScalarT, Expression]
