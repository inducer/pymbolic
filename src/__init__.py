import parser
import compiler

import pymbolic.mapper.evaluator
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency
import pymbolic.mapper.substitutor
import pymbolic.mapper.differentiator
import pymbolic.primitives

var = pymbolic.primitives.Variable
const = pymbolic.primitives.Constant

parse = pymbolic.parser.parse
evaluate = pymbolic.mapper.evaluator.evaluate
compile = pymbolic.compiler.compile
stringify = pymbolic.mapper.stringifier.stringify
is_constant = pymbolic.mapper.dependency.is_constant
get_dependencies = pymbolic.mapper.dependency.get_dependencies
substitute = pymbolic.mapper.substitutor.substitute
differentiate = pymbolic.mapper.differentiator.differentiate

if __name__ == "__main__":
    import math
    ex = parse("0 + 4.3e3j * alpha * math.cos(x+math.pi)") + 5

    print ex
    print evaluate(ex, {"alpha":5, "math":math, "x":-math.pi})
    compiled = compile(substitute(ex, {var("alpha"): const(5)}))
    print compiled(-math.pi)

    print hash(ex)
    print is_constant(ex)
    print substitute(ex, {"alpha": ex})
    ex2 = parse("cos(x**2/x)")
    print ex2
    print differentiate(ex2, parse("x"))

