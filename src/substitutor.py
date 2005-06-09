import mapper




class SubstitutionMapper(mapper.IdentityMapper):
    def __init__(self, variable_assignments):
        self.Assignments = variable_assignments

    def map_variable(self, expr):
        try:
            return self.Assignments[expr.Name]
        except KeyError:
            return expr



  
def substitute(expression, variable_assignments = {}):
    return expression.invoke_mapper(SubstitutionMapper(variable_assignments))
