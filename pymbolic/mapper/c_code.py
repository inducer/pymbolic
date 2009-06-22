from pymbolic.mapper.stringifier import SimplifyingSortingStringifyMapper




class CCodeMapper(SimplifyingSortingStringifyMapper):
    def __init__(self, constant_mapper=repr, reverse=True, 
            cse_prefix="_cse", complex_constant_base_type="double"):
        SimplifyingSortingStringifyMapper.__init__(self, constant_mapper, reverse)
        self.cse_prefix = cse_prefix
        self.cses = []
        self.cse_to_index = {}

        self.complex_constant_base_type = complex_constant_base_type

    # mappings ----------------------------------------------------------------
    def map_constant(self, x, enclosing_prec):
        import numpy
        if isinstance(x, complex):
            return "std::complex<%s>(%s, %s)" % (
                    self.complex_constant_base_type,
                    self.constant_mapper(x.real), 
                    self.constant_mapper(x.imag))
        else:
            return SimplifyingSortingStringifyMapper.map_constant(
                    self, x, enclosing_prec)

    def map_call(self, expr, enclosing_prec):
        from pymbolic.primitives import Variable
        from pymbolic.mapper.stringifier import PREC_NONE, PREC_CALL
        if isinstance(expr.function, Variable):
            func = expr.function.name
        else:
            func = self.rec(expr.function, PREC_CALL)

        return self.format("%s(%s)",
                func, self.join_rec(", ", expr.parameters, PREC_NONE))

    def map_power(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_NONE
        from pymbolic.primitives import is_constant, is_zero
        if is_constant(expr.exponent):
            if is_zero(expr.exponent):
                return "1"
            elif is_zero(expr.exponent - 1):
                return self.rec(expr.base, enclosing_prec)
            elif is_zero(expr.exponent - 2):
                return self.rec(expr.base*expr.base, enclosing_prec)

        return self.format("pow(%s, %s)",
                self.rec(expr.base, PREC_NONE), 
                self.rec(expr.exponent, PREC_NONE))

    def map_if_positive(self, expr, enclosing_prec):
        # This occurs in hedge fluxes. We cheat and define it here.
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.format("(%s > 0 ? %s : %s)",
                self.rec(expr.criterion, PREC_NONE),
                self.rec(expr.then, PREC_NONE),
                self.rec(expr.else_, PREC_NONE),
                )

    def map_common_subexpression(self, expr, enclosing_prec):
        try:
            cse_index = self.cse_to_index[expr]
        except KeyError:
            from pymbolic.mapper.stringifier import PREC_NONE
            my_cse_str = self.rec(expr.child, PREC_NONE)
            cse_index = len(self.cses)
            self.cse_to_index[expr] = cse_index
            self.cses.append(my_cse_str)

        return self.cse_prefix + str(cse_index)
