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




def make_subst_func(variable_assignments):
    import pymbolic.primitives as primitives

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

    return subst_func




def substitute(expression, variable_assignments={}, **kwargs):
    variable_assignments = variable_assignments.copy()
    variable_assignments.update(kwargs)

    return SubstitutionMapper(make_subst_func(variable_assignments))(expression)
