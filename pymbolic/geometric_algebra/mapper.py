from __future__ import annotations


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
from collections.abc import Set
from typing import ClassVar

import pymbolic.geometric_algebra.primitives as prim
from pymbolic.geometric_algebra import MultiVector
from pymbolic.mapper import (
    CachedMapper,
    CollectedT,
    Collector as CollectorBase,
    CombineMapper as CombineMapperBase,
    IdentityMapper as IdentityMapperBase,
    P,
    ResultT,
    WalkMapper as WalkMapperBase,
)
from pymbolic.mapper.constant_folder import (
    ConstantFoldingMapper as ConstantFoldingMapperBase,
)
from pymbolic.mapper.evaluator import EvaluationMapper as EvaluationMapperBase
from pymbolic.mapper.graphviz import GraphvizMapper as GraphvizMapperBase
from pymbolic.mapper.stringifier import (
    PREC_NONE,
    StringifyMapper as StringifyMapperBase,
)
from pymbolic.primitives import ExpressionNode


class IdentityMapper(IdentityMapperBase[P]):
    def map_nabla(
                self, expr: prim.Nabla, *args: P.args, **kwargs: P.kwargs
            ) -> ExpressionNode:
        return expr

    def map_nabla_component(self,
                expr: prim.NablaComponent, *args: P.args, **kwargs: P.kwargs
            ) -> ExpressionNode:
        return expr

    def map_derivative_source(self,
                expr: prim.DerivativeSource, *args: P.args, **kwargs: P.kwargs
            ) -> ExpressionNode:
        operand = self.rec(expr.operand, *args, **kwargs)
        if operand is expr.operand:
            return expr

        return type(expr)(operand, expr.nabla_id)


class CombineMapper(CombineMapperBase[ResultT, P]):
    def map_derivative_source(
                self, expr: prim.DerivativeSource, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.rec(expr.operand, *args, **kwargs)


class Collector(CollectorBase[CollectedT, P]):
    def map_nabla(self,
                expr: prim.Nabla, *args: P.args, **kwargs: P.kwargs
            ) -> Set[CollectedT]:
        return set()

    def map_nabla_component(self,
                expr: prim.NablaComponent, *args: P.args, **kwargs: P.kwargs
            ) -> Set[CollectedT]:
        return set()


class WalkMapper(WalkMapperBase[P]):
    def map_nabla(self, expr: prim.Nabla, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_nabla_component(
                self, expr: prim.NablaComponent, *args: P.args, **kwargs: P.kwargs
            ) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_derivative_source(
                self, expr, *args: P.args, **kwargs: P.kwargs
            ) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.operand, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)


class EvaluationMapper(EvaluationMapperBase):
    def map_nabla_component(self, expr):
        return expr

    map_nabla = map_nabla_component

    def map_derivative_source(self, expr):
        operand = self.rec(expr.operand)
        if operand is expr.operand:
            return expr

        return type(expr)(operand, expr.nabla_id)


class StringifyMapper(StringifyMapperBase[[]]):
    AXES: ClassVar[dict[int, str]] = {0: "x", 1: "y", 2: "z"}

    def map_nabla(self, expr, enclosing_prec):
        return f"∇[{expr.nabla_id}]"

    def map_nabla_component(self, expr, enclosing_prec):
        return "∇{}[{}]".format(
                self.AXES.get(expr.ambient_axis, expr.ambient_axis),
                expr.nabla_id)

    def map_derivative_source(self, expr, enclosing_prec):
        return r"D[{}]({})".format(expr.nabla_id, self.rec(expr.operand, PREC_NONE))


class GraphvizMapper(GraphvizMapperBase):
    def map_derivative_source(self, expr):
        self.lines.append(
                '{} [label="D[{}]",shape=ellipse];'.format(
                    self.get_id(expr), expr.nabla_id))
        if not self.visit(expr, node_printed=True):
            return

        self.rec(expr.operand)
        self.post_visit(expr)


# {{{ dimensionalizer

class Dimensionalizer(EvaluationMapper):
    """
    .. attribute:: ambient_dim

        Dimension of ambient space. Must be provided by subclass.
    """

    @property
    def ambient_dim(self):
        raise NotImplementedError

    def map_multivector_variable(self, expr):
        from pymbolic.primitives import make_sym_vector
        return MultiVector(
                make_sym_vector(expr.name, self.ambient_dim,
                    var_factory=type(expr)))

    def map_nabla(self, expr):
        from pytools.obj_array import make_obj_array
        return MultiVector(make_obj_array(
            [prim.NablaComponent(axis, expr.nabla_id)
                for axis in range(self.ambient_dim)]))

    def map_derivative_source(self, expr):
        rec_op = self.rec(expr.operand)

        if isinstance(rec_op, MultiVector):
            from pymbolic.geometric_algebra.primitives import DerivativeSource
            return rec_op.map(
                    lambda coeff: DerivativeSource(coeff, expr.nabla_id))
        else:
            return super().map_derivative_source(expr)

# }}}


# {{{ derivative binder

class DerivativeSourceAndNablaComponentCollector(CachedMapper, Collector):
    def __init__(self) -> None:
        Collector.__init__(self)
        CachedMapper.__init__(self)

    def map_nabla(self, expr):
        raise RuntimeError("DerivativeOccurrenceMapper must be invoked after "
                "Dimensionalizer--Nabla found, not allowed")

    def map_nabla_component(self, expr):
        return {expr}

    def map_derivative_source(self, expr):
        return {expr} | self.rec(expr.operand)


class NablaComponentToUnitVector(EvaluationMapper):
    def __init__(self, nabla_id, ambient_axis):
        self.nabla_id = nabla_id
        self.ambient_axis = ambient_axis

    def map_variable(self, expr):
        return expr

    def map_nabla_component(self, expr):
        if expr.nabla_id == self.nabla_id:
            if expr.ambient_axis == self.ambient_axis:
                return 1
            else:
                return 0
        else:
            return EvaluationMapper.map_nabla_component(self, expr)


class DerivativeSourceFinder(EvaluationMapper):
    """Recurses down until it finds the
    :class:`pymbolic.geometric_algebra.primitives.DerivativeSource`
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

    def __init__(self, restrict_to_id=None):
        self.derivative_collector = \
                self.derivative_source_and_nabla_component_collector()
        self.restrict_to_id = restrict_to_id

    def take_derivative(self, ambient_axis, expr):
        raise NotImplementedError

    def map_product(self, expr):
        # {{{ gather NablaComponents and DerivativeSources

        d_source_nabla_ids_per_child = []

        # id to set((child index, axis), ...)
        nabla_finder = {}
        has_d_source_nablas = False

        for child_idx, child in enumerate(expr.children):
            d_or_ns = self.derivative_collector(child)
            if not d_or_ns:
                d_source_nabla_ids_per_child.append(set())
                continue

            nabla_component_ids = set()
            derivative_source_ids = set()

            nablas = []
            for d_or_n in d_or_ns:
                if isinstance(d_or_n, prim.NablaComponent):
                    nabla_component_ids.add(d_or_n.nabla_id)
                    nablas.append(d_or_n)
                elif isinstance(d_or_n, prim.DerivativeSource):
                    derivative_source_ids.add(d_or_n.nabla_id)
                else:
                    raise RuntimeError("unexpected result from "
                            "DerivativeSourceAndNablaComponentCollector")

            d_source_nabla_ids_per_child.append(derivative_source_ids)
            if derivative_source_ids:
                has_d_source_nablas = True

            for ncomp in nablas:
                nabla_finder.setdefault(
                        ncomp.nabla_id, set()).add((child_idx, ncomp.ambient_axis))

        if nabla_finder and not any(d_source_nabla_ids_per_child):
            raise ValueError(f"no derivative source found to resolve in '{expr}'"
                    " -- did you forget to wrap the term that should have its "
                    "derivative taken in 'Derivative()(term)'?")

        if not has_d_source_nablas:
            rec_children = [self.rec(child) for child in expr.children]
            if all(rec_child is child
                    for rec_child, child in zip(
                            rec_children, expr.children, strict=True)):
                return expr

            return type(expr)(tuple(rec_children))

        # }}}

        # a list of lists, the outer level presenting a sum, the inner a product
        result = [list(expr.children)]

        for child_idx, (d_source_nabla_ids, _child) in enumerate(
                zip(d_source_nabla_ids_per_child, expr.children, strict=True)):
            if not d_source_nabla_ids:
                continue

            if len(d_source_nabla_ids) > 1:
                raise NotImplementedError("more than one DerivativeSource per "
                        "child in a product")

            nabla_id, = d_source_nabla_ids
            try:
                nablas = nabla_finder[nabla_id]
            except KeyError:
                continue

            if self.restrict_to_id is not None and nabla_id != self.restrict_to_id:
                continue

            n_axes = max(axis for _, axis in nablas) + 1

            new_result = []
            for prod_term_list in result:
                for axis in range(n_axes):
                    new_ptl = prod_term_list[:]
                    dsfinder = self.derivative_source_finder(nabla_id, self, axis)

                    new_ptl[child_idx] = dsfinder(new_ptl[child_idx])
                    for nabla_child_index, _ in nablas:
                        new_ptl[nabla_child_index] = \
                                self.nabla_component_to_unit_vector(nabla_id, axis)(
                                        new_ptl[nabla_child_index])

                    new_result.append(new_ptl)

            result = new_result

        from pymbolic.primitives import flattened_product, flattened_sum
        return flattened_sum([
                    flattened_product([
                        self.rec(prod_term) for prod_term in prod_term_list
                        ])
                    for prod_term_list in result
                    ])

    map_bitwise_xor = map_product
    map_bitwise_or = map_product
    map_left_shift = map_product
    map_right_shift = map_product

    def map_derivative_source(self, expr):
        rec_operand = self.rec(expr.operand)

        nablas = []
        for d_or_n in self.derivative_collector(rec_operand):
            if isinstance(d_or_n, prim.NablaComponent):
                nablas.append(d_or_n)
            elif isinstance(d_or_n, prim.DerivativeSource):
                pass
            else:
                raise RuntimeError("unexpected result from "
                        "DerivativeSourceAndNablaComponentCollector")

        n_axes = max(n.ambient_axis for n in nablas) + 1
        assert n_axes

        from pymbolic.primitives import flattened_sum
        return flattened_sum([
                self.take_derivative(
                    axis,
                    self.nabla_component_to_unit_vector(expr.nabla_id, axis)
                    (rec_operand))
                for axis in range(n_axes)
                ])

# }}}


class ConstantFoldingMapper(IdentityMapper, ConstantFoldingMapperBase):
    pass

# vim: foldmethod=marker
