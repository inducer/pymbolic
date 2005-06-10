import primitives




def is_zero(expr):
    # FIXME
    return isinstance(expr, primitives.Constant) and expr.Value == 0

def is_one(expr):
    return isinstance(expr, primitives.Constant) and expr.Value == 1 or is_zero(expr-1)
