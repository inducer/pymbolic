from __future__ import division

__copyright__ = "Copyright (C) 2014 Andreas Kloeckner"

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

# This is experimental, undocumented, and could go away any second.
# Consider yourself warned.

from pymbolic.geometric_algebra import MultiVector
import pymbolic.primitives as pprim
import pymbolic.geometric_algebra.primitives as prim
from pymbolic.mapper import (
        CombineMapper as CombineMapperBase,
        Collector as CollectorBase,
        IdentityMapper as IdentityMapperBase,
        WalkMapper as WalkMapperBase
        )
from pymbolic.mapper.stringifier import (
        StringifyMapper as StringifyMapperBase,
        PREC_NONE
        )
from pymbolic.mapper.evaluator import (
        EvaluationMapper as EvaluationMapperBase)


class IdentityMapper(IdentityMapperBase):
    def map_multivector_variable(self, expr):
        return expr

    map_nabla = map_multivector_variable
    map_nabla_component = map_multivector_variable

    def map_derivative_source(self, expr):
        return type(expr)(self.rec(expr.operand), expr.nabla_id)


class CombineMapper(CombineMapperBase):
    def map_derivative_source(self, expr):
        return self.rec(expr.operand)


class Collector(CollectorBase):
    def map_nabla(self, expr):
        return set()

    map_nabla_component = map_nabla


class WalkMapper(WalkMapperBase):
    def map_nabla(self, expr, *args):
        self.visit(expr, *args)

    def map_nabla_component(self, expr, *args):
        self.visit(expr, *args)

    def map_derivative_source(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.operand)


class EvaluationMapper(EvaluationMapperBase):
    def map_nabla_component(self, expr):
        return expr

    map_nabla = map_nabla_component

    def map_derivative_source(self, expr):
        return type(expr)(self.rec(expr.operand), expr.nabla_id)


class StringifyMapper(StringifyMapperBase):
    def map_nabla(self, expr, enclosing_prec):
        return r"\/[%s]" % expr.nabla_id

    def map_nabla_component(self, expr, enclosing_prec):
        return r"d/dx%d[%s]" % (expr.ambient_axis, expr.nabla_id)

    def map_derivative_source(self, expr, enclosing_prec):
        return r"D[%s](%s)" % (expr.nabla_id, self.rec(expr.operand, PREC_NONE))


# {{{ dimensionalizer

class Dimensionalizer(EvaluationMapper):
    """
    .. attribute:: ambient_dim

        Dimension of ambient space. Must be provided by subclass.
    """

    def map_multivector_variable(self, expr):
        from pymbolic.primitives import make_sym_vector
        return MultiVector(make_sym_vector(expr.name, self.ambient_dim))

    def map_nabla(self, expr):
        from pytools.obj_array import make_obj_array
        return MultiVector(make_obj_array(
            [prim.NablaComponent(axis, expr.nabla_id)
                for axis in xrange(self.ambient_dim)]))

    def map_derivative_source(self, expr):
        rec_op = self.rec(expr.operand)

        if isinstance(rec_op, MultiVector):
            from pymbolic.geometric_algebra.primitives import DerivativeSource
            return rec_op.map(
                    lambda coeff: DerivativeSource(coeff, expr.nabla_id))
        else:
            return super(Dimensionalizer, self).map_derivative_source(expr)

# }}}


# {{{ derivative binder

class DerivativeSourceAndNablaComponentCollector(Collector):
    def map_nabla(self, expr):
        raise RuntimeError("DerivativeOccurrenceMapper must be invoked after "
                "Dimensionalizer--Nabla found, not allowed")

    def map_nabla_component(self, expr):
        return set([expr])

    def map_derivative_source(self, expr):
        return set([expr])


class NablaComponentToUnitVector(EvaluationMapper):
    def __init__(self, nabla_id, ambient_axis):
        self.nabla_id = nabla_id
        self.ambient_axis = ambient_axis

    def map_nabla_component(self, expr):
        if expr.nabla_id == self.nabla_id:
            if expr.ambient_axis == self.ambient_axis:
                return 1
            else:
                return 0
        else:
            return EvaluationMapper.map_nabla_component(self, expr)


class DerivativeSourceFinder(EvaluationMapper):
    """Recurses down until it finds the :class:`pytential.sym.DerivativeSource`
    with the right *nabla_id*, then calls :method:`DerivativeBinder.take_derivative`
    on the source's argument.
    """

    def __init__(self, nabla_id, binder, ambient_axis):
        self.nabla_id = nabla_id
        self.binder = binder
        self.ambient_axis = ambient_axis

    def map_derivative_source(self, expr):
        if expr.nabla_id == self.nabla_id:
            return self.binder.take_derivative(self.ambient_axis, expr.operand)
        else:
            return EvaluationMapper.map_derivative_source(self, expr)


class DerivativeBinder(IdentityMapper):
    derivative_source_and_nabla_component_collector = \
            DerivativeSourceAndNablaComponentCollector
    nabla_component_to_unit_vector = NablaComponentToUnitVector
    derivative_source_finder = DerivativeSourceFinder

    def __init__(self):
        self.derivative_collector = \
                self.derivative_source_and_nabla_component_collector()

    def do_bind(self, rec_children):
        # We may write to this below. Make a copy.
        rec_children = list(rec_children)

        # {{{ gather NablaComponents and DerivativeSources

        d_source_nabla_ids_per_child = []

        # id to set((child index, axis), ...)
        nabla_finder = {}

        for child_idx, rec_child in enumerate(rec_children):
            nabla_component_ids = set()
            derivative_source_ids = set()

            nablas = []
            for d_or_n in self.derivative_collector(rec_child):
                if isinstance(d_or_n, prim.NablaComponent):
                    nabla_component_ids.add(d_or_n.nabla_id)
                    nablas.append(d_or_n)
                elif isinstance(d_or_n, prim.DerivativeSource):
                    derivative_source_ids.add(d_or_n.nabla_id)
                else:
                    raise RuntimeError("unexpected result from "
                            "DerivativeSourceAndNablaComponentCollector")

            d_source_nabla_ids_per_child.append(
                    derivative_source_ids - nabla_component_ids)

            for ncomp in nablas:
                nabla_finder.setdefault(
                        ncomp.nabla_id, set()).add((child_idx, ncomp.ambient_axis))

        # }}}

        # a list of lists, the outer level presenting a sum, the inner a product
        result = [rec_children]

        for child_idx, (d_source_nabla_ids, child) in enumerate(
                zip(d_source_nabla_ids_per_child, rec_children)):
            if not d_source_nabla_ids:
                continue

            if len(d_source_nabla_ids) > 1:
                raise NotImplementedError("more than one DerivativeSource per "
                        "child in a product")

            nabla_id, = d_source_nabla_ids
            nablas = nabla_finder[nabla_id]
            n_axes = max(axis for _, axis in nablas) + 1

            new_result = []
            for prod_term_list in result:
                for axis in xrange(n_axes):
                    new_ptl = prod_term_list[:]
                    dsfinder = self.derivative_source_finder(nabla_id, self, axis)

                    new_ptl[child_idx] = dsfinder(new_ptl[child_idx])
                    for nabla_child_index, _ in nablas:
                        new_ptl[nabla_child_index] = \
                                self.nabla_component_to_unit_vector(nabla_id, axis)(
                                        new_ptl[nabla_child_index])

                    new_result.append(new_ptl)

            result = new_result

        from pymbolic.primitives import flattened_sum
        return flattened_sum(
                    pprim.Product(tuple(
                        self.rec(prod_term) for prod_term in prod_term_list))
                    for prod_term_list in result)

    def map_product(self, expr):
        return self.do_bind(expr.children)

    def map_derivative_source(self, expr):
        return self.do_bind([expr])

# }}}

# vim: foldmethod=marker
