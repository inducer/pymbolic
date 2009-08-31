import pymbolic.mapper




PREC_CALL = 5
PREC_POWER = 4
PREC_UNARY = 3
PREC_PRODUCT = 2
PREC_SUM = 1
PREC_NONE = 0



class StringifyMapper(pymbolic.mapper.RecursiveMapper):
    def __init__(self, constant_mapper=str):
        self.constant_mapper = constant_mapper

    # replaceable string composition interface --------------------------------
    def format(self, s, *args):
        return s % args

    def join(self, joiner, iterable):
        return self.format(joiner.join("%s" for i in iterable), *iterable)

    def join_rec(self, joiner, iterable, prec):
        f = joiner.join("%s" for i in iterable)
        return self.format(f, *[self.rec(i, prec) for i in iterable])

    def parenthesize(self, s):
        return "(%s)" % s

    def parenthesize_if_needed(self, s, enclosing_prec, my_prec):
        if enclosing_prec > my_prec:
            return "(%s)" % s
        else:
            return s

    # mappings ----------------------------------------------------------------
    def handle_unsupported_expression(self, victim, enclosing_prec):
        strifier = victim.stringifier()
        if isinstance(self, strifier):
            raise ValueError("stringifier '%s' can't handle '%s'" 
                    % (self, victim.__class__))
        return strifier(self.constant_mapper)(victim, enclosing_prec)

    def map_constant(self, expr, enclosing_prec):
        result = self.constant_mapper(expr)

        if not (result.startswith("(") and result.endswith(")")) \
                and ("-" in result or "+" in result) \
                and (enclosing_prec > PREC_SUM):
            return self.parenthesize(result)
        else:
            return result


    def map_variable(self, expr, enclosing_prec):
        return expr.name

    def map_function_symbol(self, expr, enclosing_prec):
        return expr.__class__.__name__

    def map_call(self, expr, enclosing_prec):
        return self.format("%s(%s)",
                self.rec(expr.function, PREC_CALL),
                self.join_rec(", ", expr.parameters, PREC_NONE))

    def map_subscript(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.format("%s[%s]", 
                    self.rec(expr.aggregate, PREC_CALL), 
                    self.rec(expr.index, PREC_NONE)),
                enclosing_prec, PREC_CALL)

    def map_lookup(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.format("%s.%s", 
                    self.rec(expr.aggregate, PREC_CALL), 
                    expr.name),
                enclosing_prec, PREC_CALL)

    def map_sum(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.join_rec(" + ", expr.children, PREC_SUM),
                enclosing_prec, PREC_SUM)

    def map_product(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.join_rec("*", expr.children, PREC_PRODUCT),
                enclosing_prec, PREC_PRODUCT)

    def map_quotient(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.format("%s/%s", 
                    self.rec(expr.numerator, PREC_PRODUCT), 
                    self.rec(expr.denominator, PREC_POWER)), # analogous to ^{-1}
                enclosing_prec, PREC_PRODUCT)

    def map_power(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.format("%s**%s", 
                    self.rec(expr.base, PREC_POWER), 
                    self.rec(expr.exponent, PREC_POWER)),
                enclosing_prec, PREC_POWER)

    def map_remainder(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.format("%s %% %s", 
                    self.rec(expr.numerator, PREC_PRODUCT), 
                    self.rec(expr.denominator, PREC_POWER)), # analogous to ^{-1}
                enclosing_prec, PREC_PRODUCT)

    def map_polynomial(self, expr, enclosing_prec):
        from pymbolic.primitives import flattened_sum
        return self.rec(flattened_sum(
            [coeff*expr.base**exp for exp, coeff in expr.data[::-1]]),
            enclosing_prec)

    def map_list(self, expr, enclosing_prec):
        return self.format("[%s]", self.join_rec(", ", expr, PREC_NONE))

    map_vector = map_list

    def map_numpy_array(self, expr, enclosing_prec):
        return self.format('array(%s)', str(expr))

    def map_common_subexpression(self, expr, enclosing_prec):
        return self.format("CSE(%s)", self.rec(expr.child, PREC_NONE))

    def map_if_positive(self, expr, enclosing_prec):
        return "If(%s > 0, %s, %s)" % (
                self.rec(expr.criterion, PREC_NONE), 
                self.rec(expr.then, PREC_NONE),
                self.rec(expr.else_, PREC_NONE))




class SortingStringifyMapper(StringifyMapper):
    def __init__(self, constant_mapper=str, reverse=True):
        StringifyMapper.__init__(self, constant_mapper)
        self.reverse = reverse

    def map_sum(self, expr, enclosing_prec):
        entries = [self.rec(i, PREC_SUM) for i in expr.children]
        entries.sort(reverse=self.reverse)
        return self.parenthesize_if_needed(
                self.join(" + ", entries),
                enclosing_prec, PREC_SUM)

    def map_product(self, expr, enclosing_prec):
        entries = [self.rec(i, PREC_PRODUCT) for i in expr.children]
        entries.sort(reverse=self.reverse)
        return self.parenthesize_if_needed(
                self.join("*", entries),
                enclosing_prec, PREC_PRODUCT)




class SimplifyingSortingStringifyMapper(StringifyMapper):
    def __init__(self, constant_mapper=str, reverse=True):
        StringifyMapper.__init__(self, constant_mapper)
        self.reverse = reverse

    def map_sum(self, expr, enclosing_prec):
        def get_neg_product(expr):
            from pymbolic.primitives import is_zero, Product

            if isinstance(expr, Product) \
                    and len(expr.children) and is_zero(expr.children[0]+1):
                if len(expr.children) == 2:
                    # only the minus sign and the other child
                    return expr.children[1]
                else:
                    return Product(expr.children[1:])
            else:
                return None

        positives = []
        negatives = []

        for ch in expr.children:
            neg_prod = get_neg_product(ch)
            if neg_prod is not None:
                negatives.append(self.rec(neg_prod, PREC_PRODUCT))
            else:
                positives.append(self.rec(ch, PREC_SUM))

        positives.sort(reverse=self.reverse)
        positives = " + ".join(positives)
        negatives.sort(reverse=self.reverse)
        negatives = self.join("", 
                [self.format(" - %s", entry) for entry in negatives])

        result = positives + negatives

        return self.parenthesize_if_needed(result, enclosing_prec, PREC_SUM)

    def map_product(self, expr, enclosing_prec):
        entries = []
        i = 0
        from pymbolic.primitives import is_zero

        while i < len(expr.children):
            child = expr.children[i]
            if False and is_zero(child+1) and i+1 < len(expr.children):
                # NOTE: That space needs to be there. 
                # Otherwise two unary minus signs merge into a pre-decrement.
                entries.append(
                        self.format("- %s", self.rec(expr.children[i+1], PREC_UNARY)))
                i += 2
            else:
                entries.append(self.rec(child, PREC_PRODUCT))
                i += 1

        entries.sort(reverse=self.reverse)
        result = "*".join(entries)

        return self.parenthesize_if_needed(result, enclosing_prec, PREC_PRODUCT)
