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
        raise RuntimeError("No derivative of non-constant function "+str(func))

    def make_f(name):
        return primitives.Lookup(primitives.Variable("math"), name)

    if f is math.sin and len(pars) == 1:
        return make_f("cos")(*pars)
    elif f is math.cos and len(pars) == 1:
        return -make_f("sin")(*pars)
    elif f is math.tan and len(pars) == 1:
        return make_f("tan")(*pars)**2+1
    elif f is math.log and len(pars) == 1:
        return primitives.quotient(1, pars[0])
    elif f is math.exp and len(pars) == 1:
        return make_f("exp")(*pars)
    else:
        raise RuntimeError("unrecognized function, cannot differentiate")


class DifferentiationMapper(pymbolic.mapper.RecursiveMapper):
    """Example usage:

    .. doctest::
        :options: +NORMALIZE_WHITESPACE

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> expr = x*(x+5)**3/(x-1)**2

        >>> from pymbolic.mapper.differentiator import DifferentiationMapper as DM
        >>> print DM(x)(expr)
        (((x + 5)**3 + x*3*(x + 5)**2)*(x + -1)**2 + (-1)*2*(x + -1)*x*(x + 5)**3) \
                / (x + -1)**2**2
    """

    def __init__(self, variable, func_map=map_math_functions_by_name):
        """
        :arg variable: A :class:`pymbolic.primitives.Variable` instance
            by which to differentiate.
        :arg func_map: A function for computing derivatives of function
            calls, signature ``(arg_index, function_variable, parameters)``.
        """

        self.variable = variable
        self.function_map = func_map

    def map_constant(self, expr):
        return 0

    def map_variable(self, expr):
        if expr == self.variable:
            return 1
        else:
            return 0

    def map_call(self, expr):
        return pymbolic.flattened_sum(
            self.function_map(i, expr.function, expr.parameters)
            * self.rec(par)
            for i, par in enumerate(expr.parameters)
            )

    map_subscript = map_variable

    def map_sum(self, expr):
        return pymbolic.flattened_sum(self.rec(child) for child in expr.children)

    def map_product(self, expr):
        return pymbolic.flattened_sum(
            pymbolic.flattened_product(
                expr.children[0:i] +
                (self.rec(child),) +
                expr.children[i+1:])
            for i, child in enumerate(expr.children))

    def map_quotient(self, expr):
        f = expr.numerator
        g = expr.denominator
        df = self.rec(f)
        dg = self.rec(g)

        if (not df) and (not dg):
            return 0
        elif (not df):
            return -f*self.rec(g)/g**2
        elif (not dg):
            return self.rec(f)/g
        else:
            return (self.rec(f)*g-self.rec(g)*f)/g**2

    def map_power(self, expr):
        f = expr.base
        g = expr.exponent
        df = self.rec(f)
        dg = self.rec(g)

        log = pymbolic.var("log")

        if (not df) and (not dg):
            return 0
        elif (not df):
            return log(f) * f**g * self.rec(g)
        elif (not dg):
            return g * f**(g-1) * self.rec(f)
        else:
            return log(f) * f**g * self.rec(g) + \
                    g * f**(g-1) * self.rec(f)

    def map_polynomial(self, expr):
        # (a(x)*f(x))^n)' = a'(x)f(x)^n + a(x)f'(x)*n*f(x)^(n-1)
        deriv_coeff = []
        deriv_base = []

        dbase = self.rec(expr.base)

        for exp, coeff in expr.data:
            dcoeff = self.rec(coeff)
            if dcoeff:
                deriv_coeff.append((exp, dcoeff))
            if dbase and exp > 0:
                deriv_base.append((exp-1, exp*dbase*coeff))

        from pymbolic import Polynomial

        return \
                Polynomial(expr.base, tuple(deriv_coeff), expr.unit) + \
                Polynomial(expr.base, tuple(deriv_base), expr.unit)

    def map_numpy_array(self, expr):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            result[i] = self.rec(expr[i])
        return result


def differentiate(expression,
                  variable,
                  func_mapper=map_math_functions_by_name):
    if not isinstance(variable, (primitives.Variable, primitives.Subscript)):
        variable = primitives.make_variable(variable)
    return DifferentiationMapper(variable, func_mapper)(expression)
