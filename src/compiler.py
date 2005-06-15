import mapper.stringifier




class CompiledExpression:
    """This class is necessary to make compiled expressions picklable."""
  
    def __init__(self, expression, variable_substitutions = {}, variables = []):
        self.Expression = expression
        self.VariableSubstitutions = variable_substitutions.copy()
        self.Variables = variables[:]
        self.__compile__()

    def __compile__(self):
        # FIXME
        used_variables = sets.Set()

        def addVariable(var):
            try:
                var = self.VariableSubstitutions[var]
            except:
                pass
            used_variables.add(var)
            return var

        pythonified = mapper.stringifier.stringify(self.Expression)

        used_variables = list(used_variables)
        used_variables.sort()
        if len(self.Variables) == 0 and len(used_variables) != 0:
            variable_str = ",".join(used_variables)
        else:
            variable_str = ",".join(self.Variables)
        self.__call__ = eval("lambda %s:%s" % (variable_str, pythonified))
    
    def __getinitargs__(self):
        return self.Expression, self.VariableSubstitutions, self.Variables
        
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass




compile = CompiledExpression
