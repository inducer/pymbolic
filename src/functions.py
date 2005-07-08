import pymbolic.primitives as primitives




def sin(x):
    return primitives.Call(primitives.ElementLookup(primitives.Variable("math"), "sin"), (x,))
def cos(x):
    return primitives.Call(primitives.ElementLookup(primitives.Variable("math"), "cos"), (x,))
def tan(x):
    return primitives.Call(primitives.ElementLookup(primitives.Variable("math"), "tan"), (x,))
def log(x):
    return primitives.Call(primitives.ElementLookup(primitives.Variable("math"), "log"), (x,))
def exp(x):
    return primitives.Call(primitives.ElementLookup(primitives.Variable("math"), "exp"), (x,))

