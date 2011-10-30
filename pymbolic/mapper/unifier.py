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
    def __init__(self, mapping_candidates=None):
        self.mapping_candidates = mapping_candidates

    def unification_record_from_equation(self, lhs, rhs):
        if isinstance(lhs, (tuple, list)) or isinstance(rhs, (tuple, list)):
            # must match elementwise!
            return None

        if self.mapping_candidates is None:
            return UnificationRecord([(lhs, rhs)])
        else:
            if isinstance(lhs, Variable) and lhs.name not in self.mapping_candidates:
                return None
            if isinstance(rhs, Variable) and rhs.name not in self.mapping_candidates:
                return None
            return UnificationRecord([(lhs, rhs)])

    def map_constant(self, expr, other, unis):
        if expr == other:
            return unis
        else:
            return []

    def map_variable(self, expr, other, unis):
        new_uni_record = self.unification_record_from_equation(
                expr, other)
        if new_uni_record is None:
            if (isinstance(other, Variable) 
                    and other.name == expr.name
                    and expr.name not in self.mapping_candidates):
                return unis
            else:
                return []
        else:
            return unify_many(unis, new_uni_record)

    def map_subscript(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)

        return self.rec(expr.aggregate, other.aggregate,
                self.rec(expr.index, other.index, unis))

    def map_lookup(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)
        if self.name != other.name:
            return []

        return self.rec(expr.aggregate, other.aggregate, unis)

    def map_negation(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)
        return self.rec(expr.child, other.child, unis)

    def map_sum(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)

        if len(expr.children) != len(other.children):
            return []

        result = []

        from pytools import generate_permutations
        had_structural_match = False
        for perm in generate_permutations(range(len(expr.children))):
            it_assignments = unis

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
            return self.treat_mismatch(expr, other, unis)

        return result

    map_product = map_sum

    def map_quotient(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)

        return self.rec(expr.numerator, other.numerator,
                self.rec(expr.denominator, other.denominator, unis))

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, other, unis):
        if not isinstance(other, type(expr)):
            return self.treat_mismatch(expr, other, unis)

        return self.rec(expr.base, other.base,
                self.rec(expr.exponent, other.exponent, unis))

    def map_list(self, expr, other, unis):
        if (not isinstance(other, type(expr))
                or len(expr) != len(other)):
            return []

        for my_child, other_child in zip(expr, other):
            unis = self.rec(my_child, other_child, unis)
            if not unis:
                break

        return unis

    map_product = map_sum

    map_tuple = map_list

    def __call__(self, expr, other, unis=None):
        if unis is None:
            unis = [UnificationRecord([])]
        return self.rec(expr, other, unis)




class UnidirectionalUnifier(UnifierBase):
    """Only assigns variables encountered in the first expression to
    subexpression of the second.
    """

    def treat_mismatch(self, expr, other, unis):
        return []



class BidirectionalUnifier(UnifierBase):
    """Only assigns variables encountered in the first expression to
    subexpression of the second.
    """

    treat_mismatch = UnifierBase.map_variable
