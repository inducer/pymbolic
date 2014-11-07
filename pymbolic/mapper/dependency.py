from __future__ import division

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

from pymbolic.mapper import Collector, CSECachingMapperMixin


class DependencyMapper(CSECachingMapperMixin, Collector):
    """Maps an expression to the :class:`set` of expressions it
    is based on. The ``include_*`` arguments to the constructor
    determine which types of objects occur in this output set.
    If all are *False*, only :class:`pymbolic.primitives.Variable`
    instances are included.
    """

    def __init__(self,
            include_subscripts=True,
            include_lookups=True,
            include_calls=True,
            include_cses=False,
            composite_leaves=None):
        """
        :arg composite_leaves: Setting this is equivalent to setting
            all preceding ``include_*`` flags.
        """

        if composite_leaves is False:
            include_subscripts = False
            include_lookups = False
            include_calls = False
        if composite_leaves is True:
            include_subscripts = True
            include_lookups = True
            include_calls = True

        assert include_calls in [True, False, "descend_args"]

        self.include_subscripts = include_subscripts
        self.include_lookups = include_lookups
        self.include_calls = include_calls

        self.include_cses = include_cses

    def map_variable(self, expr):
        return set([expr])

    def map_call(self, expr):
        if self.include_calls == "descend_args":
                return self.combine(
                        [self.rec(child) for child in expr.parameters])
        elif self.include_calls:
            return set([expr])
        else:
            return super(DependencyMapper, self).map_call(expr)

    def map_call_with_kwargs(self, expr):
        if self.include_calls == "descend_args":
                return self.combine(
                        [self.rec(child) for child in expr.parameters]
                        + [self.rec(val) for name, val in expr.kw_parameters.items()]
                        )
        elif self.include_calls:
            return set([expr])
        else:
            return super(DependencyMapper, self).map_call_with_kwargs(expr)

    def map_lookup(self, expr):
        if self.include_lookups:
            return set([expr])
        else:
            return super(DependencyMapper, self).map_lookup(expr)

    def map_subscript(self, expr):
        if self.include_subscripts:
            return set([expr])
        else:
            return super(DependencyMapper, self).map_subscript(expr)

    def map_common_subexpression_uncached(self, expr):
        if self.include_cses:
            return set([expr])
        else:
            return Collector.map_common_subexpression(self, expr)

    def map_slice(self, expr):
        return self.combine(
                [self.rec(child) for child in expr.children
                    if child is not None])
