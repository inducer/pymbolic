from __future__ import annotations

from warnings import warn

from pymbolic.interop.maxima import *  # noqa: F403


warn("pymbolic.maxima is deprecated. Use pymbolic.interop.maxima instead",
     DeprecationWarning, stacklevel=1)
