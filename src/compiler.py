import sets
import math

import pymbolic
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency




class CompiledExpression:
    """This class is necessary to make compiled expressions picklable."""
  
    def __init__(self, expression, context = {"math": math}, variables = []):
        self._Expression = expression
        self._Context = context
        self._Variables = variables[:]
        self.__compile__()

    def __compile__(self):
        used_variables = pymbolic.get_dependencies(self._Expression)
        used_variables -= sets.Set(self._Variables)
        used_variables -= sets.Set(pymbolic.var(key) for key in self._Context.keys())
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = "lambda %s:%s" % (",".join(str(v) for v in all_variables), 
                                   str(self._Expression))
        print expr_s
        self.__call__ = eval(expr_s, self._Context)
    
    def __getinitargs__(self):
        return self._Expression, self._Context, self._Variables
        
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass




compile = CompiledExpression
