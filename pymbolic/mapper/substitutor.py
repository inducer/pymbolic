import pymbolic.mapper




class SubstitutionMapper(pymbolic.mapper.IdentityMapper):
    def __init__(self, subst_func):
        self.subst_func = subst_func

    def map_variable(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return expr

    def map_subscript(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return pymbolic.mapper.IdentityMapper.map_subscript(self, expr)

    def map_lookup(self, expr):
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return pymbolic.mapper.IdentityMapper.map_lookup(self, expr)



  
def substitute(expression, variable_assignments={}, **kwargs):
    import pymbolic.primitives as primitives

    variable_assignments = variable_assignments.copy()
    variable_assignments.update(kwargs)

    def subst_func(var):
        try:
            return variable_assignments[var]
        except KeyError:
            if isinstance(var, primitives.Variable):
                try:
                    return variable_assignments[var.name]
                except KeyError:
                    return None
            else:
                return None

    return SubstitutionMapper(subst_func)(expression)
