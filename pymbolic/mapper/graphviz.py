"""
.. autoclass:: GraphvizMapper
    :show-inheritance:
"""
from __future__ import annotations


__copyright__ = "Copyright (C) 2015 Andreas Kloeckner"

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

from typing import TYPE_CHECKING

from typing_extensions import Self, override

from pymbolic.mapper import WalkMapper


if TYPE_CHECKING:
    from collections.abc import Callable, Hashable

    import pymbolic.primitives as prim
    from pymbolic.geometric_algebra.primitives import Nabla, NablaComponent


class GraphvizMapper(WalkMapper[[]]):
    """Produces code for `dot <https://graphviz.org>`__ that yields
    an expression tree of the traversed expression(s).

    .. automethod:: get_dot_code

    .. versionadded:: 2015.1
    """

    lines: list[str]
    parent_stack: list[Hashable]

    next_unique_id: int
    nodes_visited: set[int]
    common_subexpressions: dict[prim.CommonSubexpression, prim.CommonSubexpression]

    def __init__(self) -> None:
        self.lines = []
        self.parent_stack = []

        self.next_unique_id = -1
        self.nodes_visited = set()
        self.common_subexpressions = {}

    def get_dot_code(self) -> str:
        """Return the dot source code for a previously traversed expression."""

        lines = "\n".join(f"  {line}" for line in self.lines)
        return f"digraph expression {{\n{lines}\n}}"

    def get_id(self, expr: object) -> str:
        """Generate a unique node ID for dot for *expr*"""

        return f"id{id(expr)}"

    def map_leaf(self, expr: prim.ExpressionNode):
        sid = self.get_id(expr)
        sexpr = str(expr).replace("\\", "\\\\")
        self.lines.append(f'{sid} [label="{sexpr}", shape=box];')

        if self.visit(expr, node_printed=True):
            self.post_visit(expr)

    def generate_unique_id(self):
        self.next_unique_id += 1
        return f"uid{self.next_unique_id}"

    @override
    def visit(self,
              expr: object, /,
              node_printed: bool = False,
              node_id: str | None = None) -> bool:
        # {{{ print connectivity

        if node_id is None:
            node_id = self.get_id(expr)

        if self.parent_stack:
            sid = self.get_id(self.parent_stack[-1])
            self.lines.append(f"{sid} -> {node_id};")

        # }}}

        if id(expr) in self.nodes_visited:
            return False
        self.nodes_visited.add(id(expr))

        if not node_printed:
            sid = self.get_id(expr)
            self.lines.append(f'{sid} [label="{type(expr).__name__}"];')

        self.parent_stack.append(expr)
        return True

    @override
    def post_visit(self, expr: object, /) -> None:
        self.parent_stack.pop(-1)

    @override
    def map_sum(self, expr: prim.Sum, /) -> None:
        sid = self.get_id(expr)
        self.lines.append(f'{sid} [label="+",shape=circle];')
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.children:
            self.rec(child)

        self.post_visit(expr)

    @override
    def map_product(self, expr: prim.Product, /) -> None:
        sid = self.get_id(expr)
        self.lines.append(f'{sid} [label="*",shape=circle];')
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.children:
            self.rec(child)

        self.post_visit(expr)

    @override
    def map_matmul(self, expr: prim.Matmul, /) -> None:
        sid = self.get_id(expr)
        self.lines.append(f'{sid} [label="@",shape=circle];')
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.children:
            self.rec(child)

        self.post_visit(expr)

    @override
    def map_variable(self, expr: prim.Variable, /) -> None:
        # Shared nodes for variables do not make for pretty graphs.
        # So we generate our own unique IDs for them.

        node_id = self.generate_unique_id()

        self.lines.append(f'{node_id} [label="{expr.name}",shape=box];')
        if not self.visit(expr, node_printed=True, node_id=node_id):
            return

        self.post_visit(expr)

    @override
    def map_lookup(self, expr: prim.Lookup, /) -> None:
        sid = self.get_id(expr)
        self.lines.append(f'{sid} [label="Lookup[{expr.name}]",shape=box];')
        if not self.visit(expr, node_printed=True):
            return

        self.rec(expr.aggregate)
        self.post_visit(expr)

    @override
    def map_constant(self, expr: object) -> None:
        # Some constants (Python ints notably) are shared among small (and
        # common) values. While accurate, this doesn't make for pretty
        # trees. So we generate our own unique IDs for them.

        node_id = self.generate_unique_id()

        self.lines.append(f'{node_id} [label="{expr}",shape=ellipse];')
        if not self.visit(expr, node_printed=True, node_id=node_id):
            return

        self.post_visit(expr)

    @override
    def map_call(self, expr: prim.Call) -> None:
        from pymbolic.primitives import Variable

        if not isinstance(expr.function, Variable):
            return super().map_call(expr)

        sid = self.get_id(expr)
        self.lines.append(f'{sid} [label="Call[{expr.function}]",shape=box];')
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.parameters:
            self.rec(child)

        self.post_visit(expr)

    @override
    def map_common_subexpression(self, expr: prim.CommonSubexpression) -> None:
        try:
            expr = self.common_subexpressions[expr]
        except KeyError:
            self.common_subexpressions[expr] = expr

        if not self.visit(expr):
            return

        self.rec(expr.child)

        self.post_visit(expr)

    # {{{ geometric algebra

    map_nabla_component: Callable[[Self, NablaComponent], None] = map_leaf
    map_nabla: Callable[[Self, Nabla], None] = map_leaf

    # }}}
