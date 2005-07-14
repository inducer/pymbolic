import sets
import math

import pymbolic
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency




class CompiledExpression:
    """This class is necessary to make compiled expressions picklable."""
  
    def __init__(self, expression, variables = []):
        self._Expression = expression
        self._Variables = variables[:]
        self.__compile__()

    def __compile__(self):
        ctx = self.context()

        used_variables = pymbolic.get_dependencies(self._Expression)
        used_variables -= sets.Set(self._Variables)
        used_variables -= sets.Set(pymbolic.var(key) for key in ctx.keys())
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = "lambda %s:%s" % (",".join(str(v) for v in all_variables), 
                                   str(self._Expression))
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
