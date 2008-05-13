import math

import pymbolic
import pymbolic.mapper.dependency
from pymbolic.mapper.stringifier import StringifyMapper, PREC_NONE, PREC_SUM, PREC_POWER




class CompileMapper(StringifyMapper):
    def __init__(self):
        StringifyMapper.__init__(self, constant_mapper=repr)

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





class CompiledExpression:
    """This class encapsulates a compiled expression.
    
    The main reason for its existence is the fact that a dynamically-constructed
    lambda function is not picklable.
    """
  
    def __init__(self, expression, variables = []):
        import pymbolic.primitives as primi

        self._Expression = expression
        self._Variables = [primi.make_variable(v) for v in variables]
        self.__compile__()

    def __compile__(self):
        ctx = self.context()

        used_variables = pymbolic.get_dependencies(self._Expression, 
                composite_leaves=False)
        used_variables -= set(self._Variables)
        used_variables -= set(pymbolic.var(key) for key in ctx.keys())
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = "lambda %s:%s" % (",".join(str(v) for v in all_variables), 
                                   CompileMapper()(self._Expression, PREC_NONE))
        self.__call__ = eval(expr_s, ctx)
    
    def __getinitargs__(self):
        return self._Expression, self._Variables
        
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass

    def context(self):
        return {"math": math}




compile = CompiledExpression
