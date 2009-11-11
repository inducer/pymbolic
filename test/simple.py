from pymbolic import parse, var
from pymbolic.mapper.dependency import DependencyMapper

x = var("x")
y = var("y")

expr2 = 3*x+5-y
expr = parse("3*x+5-y")

print expr
print expr2

dm = DependencyMapper()
print dm(expr)
