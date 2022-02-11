from pymbolic.interop.matchpy import PymbolicOp
from typing import Any, Dict, Callable


class Mapper:
    def __init__(self) -> None:
        self.cache: Dict[PymbolicOp, Any] = {}

    def rec(self, expr: PymbolicOp) -> Any:
        if expr in self.cache:
            return self.cache[expr]

        method: Callable[[PymbolicOp], Any] = getattr(self, expr._mapper_method)

        return method(expr)

    __call__ = rec
