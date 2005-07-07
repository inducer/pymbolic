import pymbolic.mapper




class SubstitutionMapper(pymbolic.mapper.IdentityMapper):
    def __init__(self, variable_assignments):
        self.Assignments = variable_assignments

    def map_variable(self, expr):
        try:
            return self.Assignments[expr]
        except KeyError:
            return expr

    def map_subscript(self, expr):
        try:
            return self.Assignments[expr]
        except KeyError:
            return pymbolic.mapper.IdentityMapper.map_subscript(self, expr)

    def map_lookup(self, expr):
        try:
            return self.Assignments[expr]
        except KeyError:
            return pymbolic.mapper.IdentityMapper.map_lookup(self, expr)



  
def substitute(expression, variable_assignments = {}):
    return expression.invoke_mapper(SubstitutionMapper(variable_assignments))
