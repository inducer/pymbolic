import pymbolic.mapper




class SubstitutionMapper(pymbolic.mapper.IdentityMapper):
    def __init__(self, variable_assignments):
        self.assignments = variable_assignments

    def map_variable(self, expr):
        try:
            return self.assignments[expr]
        except KeyError:
            return expr

    def map_subscript(self, expr):
        try:
            return self.assignments[expr]
        except KeyError:
            return pymbolic.mapper.IdentityMapper.map_subscript(self, expr)

    def map_lookup(self, expr):
        try:
            return self.assignments[expr]
        except KeyError:
            return pymbolic.mapper.IdentityMapper.map_lookup(self, expr)



  
def substitute(expression, variable_assignments = {}):
    import pymbolic.primitives as primitives

    new_var_ass = {}
    for k, v in variable_assignments.iteritems():
        new_var_ass[primitives.make_variable(k)] = v

    return SubstitutionMapper(new_var_ass)(expression)
