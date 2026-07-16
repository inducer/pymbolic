from __future__ import annotations

from warnings import warn

from pymbolic.interop.maxima import *  # ruff:ignore[undefined-local-with-import-star]


warn("pymbolic.maxima is deprecated. Use pymbolic.interop.maxima instead",
     DeprecationWarning, stacklevel=1)
