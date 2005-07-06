import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency




class CompiledExpression:
    """This class is necessary to make compiled expressions picklable."""
  
    def __init__(self, expression, variables = []):
        self._Expression = expression
        self._VariableSubstitutions = variable_substitutions.copy()
        self._Variables = variables[:]
        self.__compile__()

    def __compile__(self):
        used_variables = get_dependencies(self.Expression)
        mentioned_variables sets.Set(self._Variables)
        used_variables -= mentioned_variables
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables
      AAA FIXME sort order on Variables and Subscripts

        pythonified = mapper.stringifier.stringify(self.Expression)

        if len(self.Variables) == 0 and len(used_variables) != 0:
            variable_str = ",".join(used_variables)
        else:
            variable_str = ",".join(self.Variables)
        self.__call__ = eval("lambda %s:%s" % (variable_str, pythonified))
    
    def __getinitargs__(self):
        return self._Expression, self._VariableSubstitutions, self._Variables
        
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass




compile = CompiledExpression
