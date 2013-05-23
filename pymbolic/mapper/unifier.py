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

from pymbolic.mapper import RecursiveMapper
from pymbolic.primitives import Variable




def unify_map(map1, map2):
    result = map1.copy()
    for name, value in map2.iteritems():
        if name in map1:
            if map1[name] != value:
                return None
        else:
            result[name] = value

    return result




class UnificationRecord(object):
    def __init__(self, equations, lmap=None, rmap=None):
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

    def unify(self, other):
        new_lmap = unify_map(self.lmap, other.lmap)
        if new_lmap is None:
            return None

        new_rmap = unify_map(self.lmap, other.lmap)
        if new_rmap is None:
            return None

        return UnificationRecord(
                self.equations + other.equations,
                new_lmap, new_rmap)

    def __repr__(self):
        return "UnificationRecord(%s)" % (
                ", ".join("%s = %s" % (str(lhs), str(rhs))
                for lhs, rhs in self.equations))




def unify_many(unis1, uni2):
    result = []
    for uni1 in unis1:
        unif_result = uni1.unify(uni2)
        if unif_result is not None:
            result.append(unif_result)

    return result




class UnifierBase(RecursiveMapper):
    # The idea of the algorithm here is that the unifier accumulates a set of
    # unification possibilities (:class:`UnificationRecord`) as it descends the
    # expression tree. :func:`unify_many` above then checks if these possibilities
    # are consistent with new incoming information (also encoded as a
    # :class:`UnificationRecord`) and either augments or abandons them.

    def __init__(self, lhs_mapping_candidates=None,
            rhs_mapping_candidates=None,
            force_var_match=True):
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

    def unification_record_from_equation(self, lhs, rhs):
        if isinstance(lhs, (tuple, list)) or isinstance(rhs, (tuple, list)):
            # Always force lists/tuples to agree elementwise, never
            # generate a unification record between them directly.
            # This pushes the matching process down to the elementwise
            # level.

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

    def map_constant(self, expr, other, urecs):
        if expr == other:
            return urecs
        else:
            return []

    def map_variable(self, expr, other, urecs):
        new_uni_record = self.unification_record_from_equation(
                expr, other)

        if new_uni_record is None:
            # Check if the variables match literally--that's ok, too.
            if (isinstance(other, Variable)
                    and other.name == expr.name
                    and expr.name not in self.lhs_mapping_candidates):
                return urecs
            else:
                return []
        else:
            return unify_many(urecs, new_uni_record)

    def map_subscript(self, expr, other, urecs):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.aggregate, other.aggregate,
                self.rec(expr.index, other.index, urecs))

    def map_lookup(self, expr, other, urecs):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)
        if expr.name != other.name:
            return []

        return self.rec(expr.aggregate, other.aggregate, urecs)

    def map_sum(self, expr, other, urecs):
        if (not isinstance(other, type(expr))
                or len(expr.children) != len(other.children)):
            return []

        result = []

        from pytools import generate_permutations
        had_structural_match = False
        for perm in generate_permutations(range(len(expr.children))):
            it_assignments = urecs

            for my_child, other_child in zip(
                    expr.children,
                    (other.children[i] for i in perm)):
                it_assignments = self.rec(my_child, other_child, it_assignments)
                if not it_assignments:
                    break

            if it_assignments:
                had_structural_match = True
                result.extend(it_assignments)

        if not had_structural_match:
            return self.treat_mismatch(expr, other, urecs)

        return result

    map_product = map_sum

    def map_quotient(self, expr, other, urecs):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.numerator, other.numerator,
                self.rec(expr.denominator, other.denominator, urecs))

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, other, urecs):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, urecs)

        return self.rec(expr.base, other.base,
                self.rec(expr.exponent, other.exponent, urecs))

    def map_list(self, expr, other, urecs):
        if (not isinstance(other, type(expr))
                or len(expr) != len(other)):
            return []

        for my_child, other_child in zip(expr, other):
            urecs = self.rec(my_child, other_child, urecs)
            if not urecs:
                break

        return urecs

    map_tuple = map_list

    def __call__(self, expr, other, urecs=None):
        if urecs is None:
            urecs = [UnificationRecord([])]
        return self.rec(expr, other, urecs)




class UnidirectionalUnifier(UnifierBase):
    """Finds assignments of variables encountered in the
    first ("left") expression to subexpression of the second
    ("right") expression.
    """

    def treat_mismatch(self, expr, other, urecs):
        return []

    def map_commut_assoc(self, expr, other, urecs, factory):
        if not isinstance(other, type(expr)):
            return

        plain_cand_variables = []
        non_var_children = []
        for child in expr.children:
            if (isinstance(child, Variable)
                    and child.name in self.lhs_mapping_candidates):
                plain_cand_variables.append(child)
            else:
                non_var_children.append(child)

        # list (with indices matching non_var_children) of
        #   list of tuples (other_index, unifiers)
        unification_candidates = []

        for i, my_child in enumerate(non_var_children):
            i_matches = []
            for j, other_child in enumerate(other.children):
                result = self.rec(my_child, other_child, urecs)
                if result:
                    i_matches.append((j, result))

            unification_candidates.append(i_matches)

        def match_children(urec, next_my_idx, other_leftovers):
            if next_my_idx >= len(non_var_children):
                if not plain_cand_variables and other_leftovers:
                    return

                eqns = []
                for pv in plain_cand_variables:
                    eqns.append((pv, factory(
                        other.children[i] for i in other_leftovers)))
                    other_leftovers = []

                yield urec.unify(UnificationRecord(eqns))
                return

            for other_idx, pair_urecs in unification_candidates[next_my_idx]:
                if other_idx not in other_leftovers:
                    continue

                new_urecs = unify_many(pair_urecs, urec)
                new_rhs_leftovers = other_leftovers - set([other_idx])

                for cand_urec in new_urecs:
                    for result_urec in match_children(cand_urec, next_my_idx+1,
                            new_rhs_leftovers):
                        yield result_urec

        for urec in match_children(
                UnificationRecord([]), 0, set(range(len(other.children)))):
            yield urec

    def map_sum(self, expr, other, unis):
        from pymbolic.primitives import flattened_sum
        return list(self.map_commut_assoc(expr, other, unis, flattened_sum))

    def map_product(self, expr, other, unis):
        from pymbolic.primitives import flattened_product
        return list(self.map_commut_assoc(expr, other, unis, flattened_product))
