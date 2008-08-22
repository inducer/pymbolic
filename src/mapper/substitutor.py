import pymbolic.mapper




class SubstitutionMapperBase(object):
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



  
class SubstitutionMapper(SubstitutionMapperBase, 
        pymbolic.mapper.IdentityMapper):
    pass




def substitute(expression, variable_assignments = {},
        mapper_class=SubstitutionMapper):
    import pymbolic.primitives as primitives

    new_var_ass = {}
    for k, v in variable_assignments.iteritems():
        new_var_ass[primitives.make_variable(k)] = v

    return mapper_class(new_var_ass)(expression)
