from __future__ import annotations


__copyright__ = "Copyright (C) 2021 Thomas Gibson"

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

from pymbolic.mapper import IdentityMapper


class SubstitutionApplier(IdentityMapper):
    """todo.
    """

    def map_substitution(self, expr, current_substs):
        new_substs = current_substs.copy()
        new_substs.update(
            {variable: self.rec(value, current_substs)
            for variable, value in zip(expr.variables, expr.values)})
        return self.rec(expr.child, new_substs)

    def map_variable(self, expr, current_substs):
        return current_substs.get(expr.name, expr)

    def __call__(self, expr):
        current_substs = {}
        return super().__call__(expr, current_substs)
