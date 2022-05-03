"""
.. autoclass:: SubstitutionMapper
.. autoclass:: CachedSubstitutionMapper
.. autofunction:: make_subst_func
.. autofunction:: substitute

"""
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

from pymbolic.mapper import IdentityMapper, CachedIdentityMapper


class SubstitutionMapper(IdentityMapper):
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
            return IdentityMapper.map_subscript(self, expr)

    def map_lookup(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return IdentityMapper.map_lookup(self, expr)


class CachedSubstitutionMapper(CachedIdentityMapper,
                               SubstitutionMapper):
    def __init__(self, subst_func):
        CachedIdentityMapper.__init__(self)
        SubstitutionMapper.__init__(self, subst_func)


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


def substitute(expression, variable_assignments=None,
               mapper_cls=CachedSubstitutionMapper, **kwargs):
    """
    :arg mapper_cls: A :class:`type` of the substitution mapper
        whose instance applies the substitution.
    """
    if variable_assignments is None:
        variable_assignments = {}
    variable_assignments = variable_assignments.copy()
    variable_assignments.update(kwargs)

    return mapper_cls(make_subst_func(variable_assignments))(expression)
