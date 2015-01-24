from __future__ import division

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

from pymbolic.mapper import WalkMapper


class GraphvizMapper(WalkMapper):
    """Produces code for `dot <http://graphviz.org>`_ that yields
    an expression tree of the traversed expression(s).

    .. automethod:: get_dot_code

    .. versionadded:: 2015.1
    """

    def __init__(self):
        self.lines = []
        self.parent_stack = []

        self.next_unique_id = -1

    def get_dot_code(self):
        """Return the dot source code for a previously traversed expression."""

        return "digraph expression {\n%s\n}" % (
            "\n".join("  "+l for l in self.lines))

    def get_id(self, expr):
        "Generate a unique node ID for dot for *expr*"

        return "id%d" % id(expr)

    def generate_unique_id(self):
        self.next_unique_id += 1
        return "uid%d" % self.next_unique_id

    def visit(self, expr, node_printed=False, node_id=None):
        if node_id is None:
            node_id = self.get_id(expr)

        if not node_printed:
            self.lines.append(
                    "%s [label=\"%s\"];" % (
                        self.get_id(expr),
                        type(expr).__name__))

        if self.parent_stack:
            self.lines.append("%s -> %s;" % (
                self.get_id(self.parent_stack[-1]),
                node_id))

        self.parent_stack.append(expr)
        return True

    def post_visit(self, expr):
        self.parent_stack.pop(-1)

    def map_sum(self, expr):
        self.lines.append(
                "%s [label=\"+\",shape=circle];" % (self.get_id(expr)))
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.children:
            self.rec(child)

        self.post_visit(expr)

    def map_product(self, expr):
        self.lines.append(
                "%s [label=\"*\",shape=circle];" % (self.get_id(expr)))
        if not self.visit(expr, node_printed=True):
            return

        for child in expr.children:
            self.rec(child)

        self.post_visit(expr)

    def map_variable(self, expr):
        self.lines.append(
                "%s [label=\"%s\", shape=box];" % (self.get_id(expr), expr.name))

        self.visit(expr, node_printed=True)
        self.post_visit(expr)

    def map_constant(self, expr):
        # Some constants (Python ints notably) are shared among small (and
        # common) values. While accurate, this doesn't make for pretty
        # trees. So we generate our own unique IDs for them.

        node_id = self.generate_unique_id()

        self.lines.append(
                "%s [label=\"%s\",shape=ellipse];" % (
                    node_id,
                    str(expr)))
        self.visit(expr, node_printed=True, node_id=node_id)
        self.post_visit(expr)
