import math

import pymbolic
from pymbolic.mapper.stringifier import StringifyMapper, PREC_NONE, PREC_SUM, PREC_POWER




def _constant_mapper(c):
    # work around numpy bug #1137 (locale-sensitive repr)
    # http://projects.scipy.org/numpy/ticket/1137
    try:
        import numpy
    except ImportError:
        pass
    else:
        if isinstance(c, numpy.floating):
            c = float(c)
        elif isinstance(c, numpy.complexfloating):
            c = complex(c)

    return repr(c)


class CompileMapper(StringifyMapper):
    def __init__(self):
        StringifyMapper.__init__(self,
                constant_mapper=_constant_mapper)

    def map_polynomial(self, expr, enclosing_prec):
        # Use Horner's scheme to evaluate the polynomial

        sbase = self(expr.base, PREC_POWER)
        def stringify_exp(exp):
            if exp == 0:
                return ""
            elif exp == 1:
                return "*%s" % sbase
            else:
                return "*%s**%s" % (sbase, exp)

        result = ""
        rev_data = expr.data[::-1]
        for i, (exp, coeff) in enumerate(rev_data):
            if i+1 < len(rev_data):
                next_exp = rev_data[i+1][0]
            else:
                next_exp = 0
            result = "(%s+%s)%s" % (result, self(coeff, PREC_SUM),
                    stringify_exp(exp-next_exp))
        #print "A", result
        #print "B", expr

        if enclosing_prec > PREC_SUM and len(expr.data) > 1:
            return "(%s)" % result
        else:
            return result

    def map_numpy_array(self, expr, enclosing_prec):
        def stringify_leading_dimension(ary):
            if len(ary.shape) == 1:
                def rec(expr):
                    return self.rec(expr, PREC_NONE)
            else:
                rec = stringify_leading_dimension

            return "[%s]" % (", ".join(rec(x) for x in ary))

        return "numpy.array(%s)" % stringify_leading_dimension(expr)

    def map_foreign(self, expr, enclosing_prec):
        return StringifyMapper.map_foreign(self, expr, enclosing_prec)





class CompiledExpression:
    """This class encapsulates a compiled expression.

    The main reason for its existence is the fact that a dynamically-constructed
    lambda function is not picklable.
    """

    def __init__(self, expression, variables = []):
        import pymbolic.primitives as primi

        self._Expression = expression
        self._Variables = [primi.make_variable(v) for v in variables]
        self._compile()

    def _compile(self):
        ctx = self.context().copy()

        try:
            import numpy
        except ImportError:
            pass
        else:
            ctx["numpy"] = numpy

        from pymbolic.mapper.dependency import DependencyMapper
        used_variables = DependencyMapper(
                composite_leaves=False)(self._Expression)
        used_variables -= set(self._Variables)
        used_variables -= set(pymbolic.var(key) for key in ctx.keys())
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = CompileMapper()(self._Expression, PREC_NONE)
        func_s = "lambda %s: %s" % (",".join(str(v) for v in all_variables),
                expr_s)
        self.__call__ = eval(func_s, ctx)

    def __getinitargs__(self):
        return self._Expression, self._Variables

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass

    def context(self):
        return {"math": math}




compile = CompiledExpression
