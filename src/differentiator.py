import constant_detector
import evaluator
import primitives
import mapper
import math




def map_math_functions_by_name(i, func, pars):
    if not isinstance(func, primitives.Constant):
        raise RuntimeError, "No derivative of non-constant function "+str(func)
    name = func.Name

    if name == "sin" and len(pars) == 1:
        return primitives.Constant("cos")(pars)
    elif name == "cos" and len(pars) == 1:
        return -primitives.Constant("sin")(pars)
    elif name == "tan" and len(pars) == 1:
        return primitives.Constant("tan")(pars)**2+1
    elif name == "log" and len(pars) == 1:
        return primitives.Constant(1)/pars[0]
    elif name == "exp" and len(pars) == 1:
        return primitives.Constant("exp")(pars)
    else
        return primitives.Constant(name+"'")(pars)


class DifferentiationMapper(mapper.IdentityMapper):
    def __init__(self, variable, parameters=[], func_map):
        self.Variable = variable
        self.Parameters = parameters
        self.FunctionMap = func_map

    def map_constant(self, expr):
        return primitives.Constant(0)

    def map_variable(self, expr):
        if expr.Name is self.Variable:
            return primitives.Constant(1)
        elif expr.Name in self.Parameters:
            return expr
        else:
            return primitives.Constant(0)

    def Call(self, expr):
        result = tuple(
            self.FunctionMap(i, expr.Function, expr.Parameters)
            * par.invoke_mapper(self)
            for i, par in enumerate(expr.Parameters)
            if not self._isc(par))

        if len(result) == 0:
            return primitives.Constant(0)
        elif len(result) == 1:
            return result[0]
        else:
            return primitives.Sum(result)

    def map_product(self, expr):
        result = tuple(
            Primitives.Product(
            expr.Children[0:i] +
            child.invoke_mapper(+
            expr.Children[i+1:]
            for i, child in enumerate(expr.Children)
            if not self._isc(child))

        if len(result) == 0:
            return primitives.Constant(0)
        elif len(result) == 1:
            return result[0]
        else:
            return primitives.Sum(result)


    def map_quotient(self, expr):
        f = expr.Child1
        g = expr.Child2
        f_const = self._isc(f)
        g_const = self._isc(g)

        if f_const and g_const:
            return primitives.Constant(0)
        elif f_const:
            f = self._eval(f)
            return -f*g.invoke_mapper(self)/g**2
        elif g_const:
            g = self._eval(g)
            return f.invoke_mapper(self)/g
        else:
            return (f.invoke_mapper(self)*g-g.invoke_mapper(self)*f)/g**2

    def map_power(self, expr):
        f = expr.Child1
        g = expr.Child2
        f_const = self._isc(f)
        g_const = self._isc(g)

        log = primitives.Constant("log")

        if f_const and g_const:
            return primitives.Constant(0)
        elif f_const:
            f = self._eval(f)
            return log(f) * f**g * g.invoke_mapper(self)
        elif g_const:
            g = self._eval(g)
            return g * f**(g-1) * f.invoke_mapper(self)
        else:
            return log(f) * f**g * g.invoke_mapper(self) + \
                   g * f**(g-1) * f.invoke_mapper(self)

    def map_polynomial(self, expr):
        raise NotImplementedError
    
    def _isc(subexp):
        return constant_detector.is_constant(subexp, [self.Variable])

    def _eval(subexp):
        try:
            return primitives.Constant(evaluator.evaluate(subexp))
        except KeyError:
            return subexp
  



def differentiate(expression, variable, func_mapper=map_math_functions_by_name):
    return expression.invoke_mapper(DifferentiationMapper(variable))
