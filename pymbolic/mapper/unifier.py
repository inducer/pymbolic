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

from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, final

from typing_extensions import Self, override

from pymbolic.mapper import Mapper
from pymbolic.primitives import Variable
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    import pymbolic.primitives as p


def unify_map(
            map1: Mapping[str, Expression],
            map2: Mapping[str, Expression]
        ) -> Mapping[str, Expression] | None:
    result = dict(map1)
    for name, value in map2.items():
        if name in map1:
            if map1[name] != value:
                return None
        else:
            result[name] = value

    return result


@final
class UnificationRecord:
    """
    .. autoattribute:: lmap
    .. autoattribute:: rmap
    .. automethod:: unify
    """

    lmap: Mapping[str, Expression]
    rmap: Mapping[str, Expression]

    def __init__(self,
            equations: Collection[tuple[Expression, Expression]],
            lmap: Mapping[str, Expression] | None = None,
            rmap: Mapping[str, Expression] | None = None) -> None:
        self.equations = equations

        # lmap and rmap just serve as a tool to reject
        # some unifications early.

        if lmap is None or rmap is None:
            lmap = {}
            rmap = {}

            for lhs, rhs in equations:
                if isinstance(lhs, Variable):
                    lmap[lhs.name] = rhs
                if isinstance(rhs, Variable):
                    rmap[rhs.name] = lhs

        self.lmap = lmap
        self.rmap = rmap

    def unify(self, other: UnificationRecord | None) -> UnificationRecord | None:
        if other is None:
            return None

        new_lmap = unify_map(self.lmap, other.lmap)
        if new_lmap is None:
            return None

        new_rmap = unify_map(self.rmap, other.rmap)
        if new_rmap is None:
            return None

        # Merge redundant equations.
        new_equations = set(self.equations)
        new_equations.update(other.equations)

        return UnificationRecord(
            list(new_equations), new_lmap, new_rmap)

    @override
    def __repr__(self) -> str:
        eqs = ", ".join(f"{lhs} = {rhs}" for lhs, rhs in self.equations)
        return f"{type(self).__name__}({eqs})"


def unify_many(
            unis1: Sequence[UnificationRecord],
            uni2: UnificationRecord
        ) -> Sequence[UnificationRecord]:
    result: list[UnificationRecord] = []
    for uni1 in unis1:
        unif_result = uni1.unify(uni2)
        if unif_result is not None:
            result.append(unif_result)

    return result


class UnifierBase(Mapper[
                  Sequence[UnificationRecord],
                  [Expression, Sequence[UnificationRecord]]], ABC):
    # The idea of the algorithm here is that the unifier accumulates a set of
    # unification possibilities (:class:`UnificationRecord`) as it descends the
    # expression tree. :func:`unify_many` above then checks if these possibilities
    # are consistent with new incoming information (also encoded as a
    # :class:`UnificationRecord`) and either augments or abandons them.

    lhs_mapping_candidates: Collection[str] | None
    rhs_mapping_candidates: Collection[str] | None
    force_var_match: bool

    def __init__(self,
            lhs_mapping_candidates: Collection[str] | None = None,
            rhs_mapping_candidates: Collection[str] | None = None,
            force_var_match: bool = True) -> None:
        """
        :arg lhs_mapping_candidates: list or set of  variable names that may be
          assigned in the left-hand ("first") expression
        :arg rhs_mapping_candidates: list or set of  variable names that may be
          assigned in the right-hand ("second") expression
        :arg force_var_match: In the (unimplemented) case of bidirectional
          unification, only assign to variable names, don't make matches
          between higher-level expressions.
        """

        self.lhs_mapping_candidates = lhs_mapping_candidates
        self.rhs_mapping_candidates = rhs_mapping_candidates
        self.force_var_match = force_var_match

    @abstractmethod
    def treat_mismatch(
                self,
                expr: Expression,
                other: Expression,
                urecs: Sequence[UnificationRecord]
            ) -> Sequence[UnificationRecord]:
        pass

    def unification_record_from_equation(
                self, lhs: Expression, rhs: Expression) -> UnificationRecord | None:
        if isinstance(lhs, (tuple, list)) or isinstance(rhs, (tuple, list)):
            # Always force lists/tuples to agree elementwise, never
            # generate a unification record between them directly.
            # This pushes the matching process down to the elementwise level.

            return None

        lhs_is_var = isinstance(lhs, Variable)
        rhs_is_var = isinstance(rhs, Variable)

        if self.force_var_match and not (lhs_is_var or rhs_is_var):
            return None

        if (self.lhs_mapping_candidates is not None
                and lhs_is_var
                and lhs.name not in self.lhs_mapping_candidates):
            return None
        if (self.rhs_mapping_candidates is not None
                and rhs_is_var
                and rhs.name not in self.rhs_mapping_candidates):
            return None

        return UnificationRecord([(lhs, rhs)])

    @override
    def map_constant(
                self,
                expr: object,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if expr == other:
            return urecs
        else:
            return []

    @override
    def map_variable(
                self,
                expr: p.Variable,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        new_uni_record = self.unification_record_from_equation(
                expr, other)

        if new_uni_record is None:
            # Check if the variables match literally--that's ok, too.
            if (isinstance(other, Variable) and other.name == expr.name
                    and (
                        self.lhs_mapping_candidates is None
                        or expr.name not in self.lhs_mapping_candidates)):
                return urecs
            else:
                return []
        else:
            return unify_many(urecs, new_uni_record)

    @override
    def map_call(self,
                 expr: p.Call,
                 other: Expression,
                 urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.function, other.function,
                self.rec(expr.parameters, other.parameters, urecs))

    @override
    def map_subscript(
                self,
                expr: p. Subscript,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        # {{{ unpack length-1 index tuples to avoid ambiguity

        expr_index = expr.index
        if isinstance(expr_index, tuple) and len(expr_index) == 1:
            expr_index, = expr_index

        other_index = other.index
        if isinstance(other_index, tuple) and len(other_index) == 1:
            other_index, = other_index

        # }}}

        return self.rec(expr.aggregate, other.aggregate,
                self.rec(expr_index, other_index, urecs))

    @override
    def map_lookup(
                self,
                expr: p.Lookup,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)
        if expr.name != other.name:
            return []

        return self.rec(expr.aggregate, other.aggregate, urecs)

    @override
    def map_sum(self,
                expr: (
                    p.Sum | p.Product
                    | p.BitwiseAnd | p.BitwiseOr | p.BitwiseXor
                    | p.LogicalAnd | p.LogicalOr
                    | p.Min | p.Max),
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if (not isinstance(other, type(expr))
                or len(expr.children) != len(other.children)):
            return []

        result: list[UnificationRecord] = []

        from pytools import generate_permutations
        had_structural_match = False
        for perm in generate_permutations(list(range(len(expr.children)))):
            it_assignments = urecs

            for my_child, other_child in zip(
                    expr.children,
                    (other.children[i] for i in perm), strict=True):
                it_assignments = self.rec(my_child, other_child, it_assignments)
                if not it_assignments:
                    break

            if it_assignments:
                had_structural_match = True
                result.extend(it_assignments)

        if not had_structural_match:
            return self.treat_mismatch(expr, other, urecs)

        return result

    map_product: Callable[[Self, p.Product, Expression, Sequence[UnificationRecord]],
                          Sequence[UnificationRecord]] = map_sum

    @override
    def map_quotient(
                self,
                expr: p.Quotient | p.FloorDiv | p.Remainder,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.numerator, other.numerator,
                self.rec(expr.denominator, other.denominator, urecs))

    map_floor_div: Callable[[Self, p.FloorDiv, Expression, Sequence[UnificationRecord]],
                            Sequence[UnificationRecord]] = map_quotient
    map_remainder: Callable[[Self, p.Remainder, Expression, Sequence[UnificationRecord]],  # noqa: E501
                            Sequence[UnificationRecord]] = map_quotient

    @override
    def map_power(
                self,
                expr: p.Power,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.base, other.base,
                self.rec(expr.exponent, other.exponent, urecs))

    @override
    def map_left_shift(
                self,
                expr: p.LeftShift | p.RightShift,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.shiftee, other.shiftee,
                self.rec(expr.shift, other.shift, urecs))

    map_right_shift: Callable[[Self, p.RightShift, Expression, Sequence[UnificationRecord]],  # noqa: E501
                              Sequence[UnificationRecord]] = map_left_shift

    @override
    def map_bitwise_not(
                self,
                expr: p.BitwiseNot | p.LogicalNot,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.child, other.child, urecs)

    map_bitwise_or: Callable[[Self, p.BitwiseOr, Expression, Sequence[UnificationRecord]],  # noqa: E501
                             Sequence[UnificationRecord]] = map_sum
    map_bitwise_xor: Callable[[Self, p.BitwiseXor, Expression, Sequence[UnificationRecord]],  # noqa: E501
                              Sequence[UnificationRecord]] = map_sum
    map_bitwise_and: Callable[[Self, p.BitwiseAnd, Expression, Sequence[UnificationRecord]],  # noqa: E501
                              Sequence[UnificationRecord]] = map_sum

    map_logical_not: Callable[[Self, p.LogicalNot, Expression, Sequence[UnificationRecord]],  # noqa: E501
                             Sequence[UnificationRecord]] = map_bitwise_not
    map_logical_or: Callable[[Self, p.LogicalOr, Expression, Sequence[UnificationRecord]],  # noqa: E501
                             Sequence[UnificationRecord]] = map_sum
    map_logical_and: Callable[[Self, p.LogicalAnd, Expression, Sequence[UnificationRecord]],  # noqa: E501
                              Sequence[UnificationRecord]] = map_sum

    @override
    def map_comparison(
                self,
                expr: p.Comparison,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if (not isinstance(other, type(expr))
                or expr.operator != other.operator):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.left, other.left,
                self.rec(expr.right, other.right, urecs))

    @override
    def map_if(
                self,
                expr: p.If,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.condition, other.condition,
                self.rec(expr.then, other.then,
                    self.rec(expr.else_, other.else_, urecs)))

    map_min: Callable[[Self, p.Min, Expression, Sequence[UnificationRecord]],
                      Sequence[UnificationRecord]] = map_sum
    map_max: Callable[[Self, p.Max, Expression, Sequence[UnificationRecord]],
                      Sequence[UnificationRecord]] = map_sum

    @override
    def map_list(self,
                 expr: Sequence[Expression],
                 other: Expression,
                 urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        if (not isinstance(other, type(expr)) or len(expr) != len(other)):
            return []

        for my_child, other_child in zip(expr, other, strict=True):
            urecs = self.rec(my_child, other_child, urecs)
            if not urecs:
                break

        return urecs

    map_tuple: Callable[[Self, tuple[Expression, ...], Expression, Sequence[UnificationRecord]],  # noqa: E501
                        Sequence[UnificationRecord]] = map_list

    @override
    def __call__(self,
                 expr: Expression,
                 other: Expression,
                 urecs: Sequence[UnificationRecord] | None = None,
                 ) -> Sequence[UnificationRecord]:
        if urecs is None:
            urecs = [UnificationRecord([])]

        return self.rec(expr, other, urecs)


class UnidirectionalUnifier(UnifierBase):
    """Finds assignments of variables encountered in the
    first ("left") expression to subexpression of the second
    ("right") expression.
    """

    @override
    def treat_mismatch(
                self,
                expr: Expression,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        return []

    def map_commut_assoc(
                self,
                expr: p.Sum | p.Product,
                other: Expression,
                urecs: Sequence[UnificationRecord],
                factory: Callable[[Iterable[ArithmeticExpression]],
                                   ArithmeticExpression],
                ) -> Iterator[UnificationRecord]:
        if not isinstance(other, type(expr)):
            return

        # Partition expr into terms that are plain (free) variables and those
        # that are not.
        plain_var_candidates: list[Variable] = []
        non_var_children: list[Expression] = []
        for child in expr.children:
            if (isinstance(child, Variable)
                    and (
                        self.lhs_mapping_candidates is None
                        or child.name in self.lhs_mapping_candidates)):
                plain_var_candidates.append(child)
            else:
                non_var_children.append(child)

        # list (with indices matching non_var_children) of
        #   list of tuples (other_index, unifiers)
        unification_candidates: list[list[tuple[int, Sequence[UnificationRecord]]]] = []

        # Unify non-free-variable children of expr with children of the other
        # expr.
        for my_child in non_var_children:
            i_matches: list[tuple[int, Sequence[UnificationRecord]]] = []
            for j, other_child in enumerate(other.children):
                result = self.rec(my_child, other_child, urecs)
                if result:
                    i_matches.append((j, result))

            unification_candidates.append(i_matches)

        # Combine the unification candidates of children in all possible ways.
        def match_children(
                    urec: UnificationRecord,
                    next_cand_idx: int,
                    other_leftovers: set[int]) -> Iterator[UnificationRecord]:
            if next_cand_idx >= len(non_var_children):
                yield from match_plain_var_candidates(urec, other_leftovers)
                return

            for other_idx, pair_urecs in unification_candidates[next_cand_idx]:
                if other_idx not in other_leftovers:
                    # Don't re-match any elements.
                    continue

                new_urecs = unify_many(pair_urecs, urec)
                new_rhs_leftovers = other_leftovers - {other_idx}

                for cand_urec in new_urecs:
                    yield from match_children(
                            cand_urec, next_cand_idx + 1, new_rhs_leftovers)

        def match_plain_var_candidates(
                    urec: UnificationRecord,
                    other_leftovers: set[int]) -> Iterator[UnificationRecord]:
            if len(plain_var_candidates) == len(other_leftovers) == 0:
                yield urec
                return

            # At this point, the values in plain_var_candidates have not
            # been matched in the lhs, and the values in other_leftovers
            # have not been matched in the rhs. Try all possible
            # combinations of matches (this part may become a performance
            # bottleneck and if needed could be optimized further).
            def subsets(s: set[int], max_size: int) -> Iterator[tuple[int, ...]]:
                from itertools import combinations
                for size in range(1, max_size + 1):
                    yield from combinations(s, size)

            def partitions(s: set[int], k: int) -> Iterator[list[set[int]]]:
                if k == 1:
                    yield [s]
                    return
                for subset in map(set, subsets(s, len(s) - k + 1)):
                    for partition in partitions(s - subset, k - 1):
                        yield [subset, *partition]

            for partition in partitions(
                    other_leftovers,
                    len(plain_var_candidates)):
                result = urec
                for subset, var in zip(partition, plain_var_candidates, strict=True):
                    rec = self.unification_record_from_equation(
                        var, factory(other.children[i] for i in subset))
                    result = result.unify(rec)
                    if not result:
                        break
                else:
                    if len(non_var_children) != 0:
                        # urecs was merged in.
                        yield result
                        return
                    # urecs was not merged in, do it here.
                    yield from unify_many(urecs, result)

        yield from match_children(
            UnificationRecord([]),
            0,
            set(range(len(other.children))))

    @override
    def map_sum(self,  # pyright: ignore[reportIncompatibleMethodOverride]
                expr: p.Sum,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        from pymbolic.primitives import flattened_sum
        return list(self.map_commut_assoc(expr, other, urecs, flattened_sum))

    @override
    def map_product(
                self,
                expr: p.Product,
                other: Expression,
                urecs: Sequence[UnificationRecord]) -> Sequence[UnificationRecord]:
        from pymbolic.primitives import flattened_product
        return list(self.map_commut_assoc(expr, other, urecs, flattened_product))
