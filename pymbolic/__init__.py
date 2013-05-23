from __future__ import division

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""




import parser
import compiler

import pymbolic.mapper.evaluator
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency
import pymbolic.mapper.substitutor
import pymbolic.mapper.differentiator
import pymbolic.mapper.expander
import pymbolic.mapper.flattener
import pymbolic.primitives

from pymbolic.polynomial import Polynomial

var = pymbolic.primitives.Variable
variables = pymbolic.primitives.variables
flattened_sum = pymbolic.primitives.flattened_sum
subscript = pymbolic.primitives.subscript
flattened_product = pymbolic.primitives.flattened_product
quotient = pymbolic.primitives.quotient
linear_combination = pymbolic.primitives.linear_combination
cse = pymbolic.primitives.make_common_subexpression
make_sym_vector = pymbolic.primitives.make_sym_vector

parse = pymbolic.parser.parse
evaluate = pymbolic.mapper.evaluator.evaluate
evaluate_kw = pymbolic.mapper.evaluator.evaluate_kw
compile = pymbolic.compiler.compile
substitute = pymbolic.mapper.substitutor.substitute
differentiate = pymbolic.mapper.differentiator.differentiate
expand = pymbolic.mapper.expander.expand
flatten = pymbolic.mapper.flattener.flatten




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

    x0 = parse("x[0]")
    ex = parse("1-x[0]")
    print differentiate(ex, x0)
    #print expand(ex)

