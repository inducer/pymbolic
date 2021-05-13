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

import pymbolic.mapper


class SubstitutionMapper(pymbolic.mapper.IdentityMapper):
    def __init__(self, subst_func):
        self.subst_func = subst_func

    def map_variable(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return expr

    def map_subscript(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return pymbolic.mapper.IdentityMapper.map_subscript(self, expr)

    def map_lookup(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return pymbolic.mapper.IdentityMapper.map_lookup(self, expr)


def make_subst_func(variable_assignments):
    import pymbolic.primitives as primitives

    def subst_func(var):
        try:
            return variable_assignments[var]
        except KeyError:
            if isinstance(var, primitives.Variable):
                try:
                    return variable_assignments[var.name]
                except KeyError:
                    return None
            else:
                return None

    return subst_func


def substitute(expression, variable_assignments=None, **kwargs):
    if variable_assignments is None:
        variable_assignments = {}
    variable_assignments = variable_assignments.copy()
    variable_assignments.update(kwargs)

    return SubstitutionMapper(make_subst_func(variable_assignments))(expression)
