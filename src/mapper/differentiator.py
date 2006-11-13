import math
import cmath

import pymbolic
import pymbolic.primitives as primitives
import pymbolic.mapper
import pymbolic.mapper.evaluator



def map_math_functions_by_name(i, func, pars):
    try:
        f = pymbolic.evaluate(func, {"math": math, "cmath": cmath})
    except pymbolic.mapper.evaluator.UnknownVariableError:
        raise RuntimeError, "No derivative of non-constant function "+str(func)

    def make_f(name):
        return primitives.ElementLookup(primitives.Variable("math"), name)

    if f is math.sin and len(pars) == 1:
        return make_f("cos")(*pars)
    elif f is math.cos and len(pars) == 1:
        return -make_f("sin")(*pars)
    elif f is math.tan and len(pars) == 1:
        return make_f("tan")(*pars)**2+1
    elif f is math.log and len(pars) == 1:
        return primitives.Constant(1)/pars[0]
    elif f is math.exp and len(pars) == 1:
        return make_f("exp")(*pars)
    else:
        raise RuntimeError, "unrecognized function, cannot differentiate"




class DifferentiationMapper(pymbolic.mapper.Mapper):
    def __init__(self, variable, func_map):
        self.Variable = variable
        self.FunctionMap = func_map

    def map_constant(self, expr):
        return primitives.Constant(0)

    def map_variable(self, expr):
        if expr == self.Variable:
            return primitives.Constant(1)
        else:
            return primitives.Constant(0)

    def map_call(self, expr):
        return pymbolic.sum(*(
            self.FunctionMap(i, expr.function, expr.parameters)
            * self(par)
            for i, par in enumerate(expr.parameters)
            if not self._isc(par)))

    map_subscript = map_variable

    def map_negation(self, expr):
        return -self(expr.child)

    def map_sum(self, expr):
        return pymbolic.sum(*(self(child)
                              for child in expr.children
                              if not self._isc(child)))

    def map_product(self, expr):
        return pymbolic.sum(*(
            pymbolic.product(*(expr.children[0:i] + 
                             (self(child),) +
                             expr.children[i+1:]))
            for i, child in enumerate(expr.children)
            if not self._isc(child)))

    def map_rational(self, expr):
        f = expr.numerator
        g = expr.denominator
        f_const = self._isc(f)
        g_const = self._isc(g)

        if f_const and g_const:
            return primitives.Constant(0)
        elif f_const:
            return -f*self(g)/g**2
        elif g_const:
            return self(f)/g
        else:
            return (self(f)*g-self(g)*f)/g**2

    def map_power(self, expr):
        f = expr.base
        g = expr.exponent
        f_const = self._isc(f)
        g_const = self._isc(g)

        log = primitives.Constant("log")

        if f_const and g_const:
            return primitives.Constant(0)
        elif f_const:
            return log(f) * f**g * self(g)
        elif g_const:
            return g * f**(g-1) * self(f)
        else:
            return log(f) * f**g * self(g) + \
                   g * f**(g-1) * self(f)

    def map_polynomial(self, expr):
        raise NotImplementedError
    
    def _isc(self,subexp):
        return pymbolic.is_constant(subexp, [self.Variable])
  



def differentiate(expression, 
                  variable, 
                  func_mapper=map_math_functions_by_name):
    if not isinstance(variable, (primitives.Variable, primitives.Subscript)):
        variable = primitives.make_variable(variable)
    return DifferentiationMapper(variable, func_mapper)(expression)
