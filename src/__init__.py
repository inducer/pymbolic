import parser
import compiler

import pymbolic.mapper.evaluator
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency
import pymbolic.mapper.substitutor
import pymbolic.mapper.differentiator
import pymbolic.mapper.expander
import pymbolic.primitives

var = pymbolic.primitives.Variable
sum = pymbolic.primitives.sum
subscript = pymbolic.primitives.subscript
product = pymbolic.primitives.product
quotient = pymbolic.primitives.quotient
linear_combination = pymbolic.primitives.linear_combination

parse = pymbolic.parser.parse
evaluate = pymbolic.mapper.evaluator.evaluate
compile = pymbolic.compiler.compile
is_constant = pymbolic.mapper.dependency.is_constant
get_dependencies = pymbolic.mapper.dependency.get_dependencies
substitute = pymbolic.mapper.substitutor.substitute
differentiate = pymbolic.mapper.differentiator.differentiate
expand = pymbolic.mapper.expander.expand




def simplify(x):
    # FIXME: Not yet implemented
    return x

def grad(expression, variables):
    return [differentiate(expression, var) for var in variables]

def jacobian(expression_list, variables):
    return [grad(expr, variables) for expr in expression_list]
    
def laplace(expression, variables):
    return sum(differentiate(differentiate(expression,var), var) for var in variables)




class VectorFunction:
    def __init__(self, function_list, variables=[]):
        self.FunctionList = [pymbolic.compile(expr, variables=variables) 
                             for expr in function_list]

    def __call__(self, x):
        import pylinear.array as num
        return num.array([ func(x) for func in self.FunctionList ])




class MatrixFunction:
    def __init__(self, function_list, variables=[]):
        self. FunctionList = [[pymbolic.compile(expr, variables=variables)
                               for expr in outer]
                              for outer in function_list]

    def __call__(self, x):
        import pylinear.array as num
        return num.array([[func(x) for func in flist ] for flist in self.FunctionList])




if __name__ == "__main__":
    import math
    #ex = parse("0 + 4.3e3j * alpha * math.cos(x+math.pi)") + 5

    #print ex
    #print repr(parse("x+y"))
    #print evaluate(ex, {"alpha":5, "math":math, "x":-math.pi})
    #compiled = compile(substitute(ex, {var("alpha"): 5}))
    #print compiled(-math.pi)
    #import cPickle as pickle
    #pickle.dumps(compiled)

    #print hash(ex)
    #print is_constant(ex)
    #print substitute(ex, {"alpha": ex})
    #ex2 = parse("math.cos(x**2/x)")
    #print ex2
    #print differentiate(ex2, parse("x"))

    ex = parse("(a+b)**12*(c+d)")
    print ex
    print expand(ex)

