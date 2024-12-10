from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from pymbolic.interop.matchpy import PymbolicOp


class Mapper:
    def __init__(self) -> None:
        self.cache: dict[PymbolicOp, Any] = {}

    def rec(self, expr: PymbolicOp) -> Any:
        if expr in self.cache:
            return self.cache[expr]

        method: Callable[[PymbolicOp], Any] = getattr(self, expr._mapper_method)

        return method(expr)

    __call__ = rec
