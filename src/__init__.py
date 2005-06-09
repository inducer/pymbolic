import parser
import evaluator
import compiler
import stringifier
import constant_detector
import substitutor
import differentiator

parse = parser.parse
evaluate = evaluator.evaluate
compile = compiler.compile
stringify = stringifier.stringify
is_constant = constant_detector.is_constant
substitute = substitutor.substitute
differentiate = differentiator.differentiate

if __name__ == "__main__":
    import math
    ex = parse("0 + 4.3e3j * alpha * cos(x+pi)") + 5

    print ex
    #print evaluate(ex, {"alpha":5, "cos":math.cos, "x":-math.pi, "pi":math.pi})
    #print is_constant(ex)
    #print substitute(ex, {"alpha": ex})
    ex2 = parse("cos(x**2/x)")
    print ex2
    print differentiate(ex2, "x")

