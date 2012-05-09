from __future__ import division
import pymbolic.primitives as prim
from pymbolic.mapper.evaluator import EvaluationMapper
import sympy as sp




class _SympyMapper(object):
    def __call__(self, expr, *args, **kwargs):
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr, *args, **kwargs):
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = "map_"+mro.pop(0).__name__

            try:
                method = getattr(dispatch_class, method_name)
            except AttributeError:
                pass
            else:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr):
        raise NotImplementedError(
                "%s does not know how to map type '%s'"
                % (type(self).__name__,
                    type(expr).__name__))




class CSE(sp.Function):
    """A function to translate to a Pymbolic CSE."""

    nargs = 1




def make_cse(arg, prefix=None):
    result = CSE(arg)
    result.prefix = prefix
    return result




class SympyToPymbolicMapper(_SympyMapper):
    def map_Symbol(self, expr):
        return prim.Variable(expr.name)

    def map_ImaginaryUnit(self, expr):
        return 1j

    def map_Pi(self, expr):
        return float(expr)

    def map_Add(self, expr):
        return prim.Sum(tuple(self.rec(arg) for arg in expr.args))

    def map_Mul(self, expr):
        return prim.Product(tuple(self.rec(arg) for arg in expr.args))

    def map_Rational(self, expr):
        num = self.rec(expr.p)
        denom = self.rec(expr.q)

        if prim.is_zero(denom-1):
            return num
        return prim.Quotient(num, denom)

    def map_Pow(self, expr):
        return prim.Power(self.rec(expr.base), self.rec(expr.exp))

    def map_Subs(self, expr):
        return prim.Substitution(self.rec(expr.expr),
                tuple(v.name for v in expr.variables),
                tuple(self.rec(v) for v in expr.point),
                )

    def map_Derivative(self, expr):
        return prim.Derivative(self.rec(expr.expr),
                tuple(v.name for v in expr.variables))

    def map_CSE(self, expr):
        return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr.prefix)

    def not_supported(self, expr):
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            return prim.Variable(type(expr).__name__)(
                    *tuple(self.rec(arg) for arg in expr.args))
        else:
            return _SympyMapper.not_supported(self, expr)




class PymbolicToSympyMapper(EvaluationMapper):
    def map_variable(self, expr):
        return sp.Symbol(expr.name)

    def map_call(self, expr):
        if isinstance(expr.function, prim.Variable):
            func_name = expr.function.name
            try:
                func = getattr(sp.functions, func_name)
            except AttributeError:
                func = sp.Function(func_name)
            return func(*[self.rec(par) for par in expr.parameters])
        else:
            raise RuntimeError("do not know how to translate '%s' to sympy"
                    % expr)

    def map_subscript(self, expr):
        if isinstance(expr.aggregate, prim.Variable) and isinstance(expr.index, int):
            return sp.Symbol("%s_%d" % (expr.aggregate.name, expr.index))
        else:
            raise RuntimeError("do not know how to translate '%s' to sympy"
                    % expr)
