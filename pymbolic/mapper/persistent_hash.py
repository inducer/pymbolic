from __future__ import annotations


__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


from warnings import warn

from pymbolic.mapper import WalkMapper


class PersistentHashWalkMapper(WalkMapper):
    """A subclass of :class:`pymbolic.mapper.WalkMapper` for constructing
    persistent hash keys for use with
    :class:`pytools.persistent_dict.PersistentDict`.
    """

    def __init__(self, key_hash):
        self.key_hash = key_hash

        warn("PersistentHashWalkMapper is deprecated. "
             "Since they are dataclasses, expression objects should now "
             "support persistent hashing natively without any help. "
             "It will be removed in 2026.",
             DeprecationWarning, stacklevel=2)

    def visit(self, expr):
        self.key_hash.update(type(expr).__name__.encode("utf8"))
        return True

    def map_variable(self, expr):
        self.key_hash.update(expr.name.encode("utf8"))

    def map_constant(self, expr):
        import sys
        if "numpy" in sys.modules:
            import numpy as np
            if isinstance(expr, np.generic):
                # Makes a Python scalar from a numpy one.
                expr = expr.item()

        self.key_hash.update(repr(expr).encode("utf8"))

    def map_comparison(self, expr):
        if self.visit(expr):
            self.rec(expr.left)
            self.key_hash.update(repr(expr.operator).encode("utf8"))
            self.rec(expr.right)
