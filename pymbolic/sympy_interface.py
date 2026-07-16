from __future__ import annotations

from warnings import warn

from pymbolic.interop.sympy import *  # ruff:ignore[undefined-local-with-import-star]


warn("pymbolic.sympy_interface is deprecated. Use pymbolic.interop.sympy instead",
     DeprecationWarning, stacklevel=1)
