from __future__ import annotations


__copyright__ = """
Copyright (C) 2013 Andreas Kloeckner
Copyright (C) 2014 Matt Wala
"""

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

import logging


logger = logging.getLogger(__name__)


# {{{ graphviz / dot export

def _default_preamble_hook():
    # Sets default attributes for nodes and edges.
    yield 'node [shape="box"];'
    yield 'edge [dir="back"];'


def get_dot_dependency_graph(
        statements,  use_stmt_ids=None,
        preamble_hook=_default_preamble_hook,
        additional_lines_hook=list,
        statement_stringifier=None,

        # deprecated
        use_insn_ids=None,):
    """Return a string in the `dot <https://graphviz.org/>`__ language depicting
    dependencies among kernel statements.

    :arg statements: A sequence of statements, each of which is stringified by
        calling *statement_stringifier*.
    :arg statement_stringifier: The function to use for stringifying the
        statements. The default stringifier uses :class:`str` and escapes all
        double quotes (``"``) in the string representation.
    :arg preamble_hook: A function that returns an iterable of lines
        to add at the beginning of the graph
    :arg additional_lines_hook: A function that returns an iterable
        of lines to add at the end of the graph

    """
    if statement_stringifier is None:
        def statement_stringifier(s):
            return str(s).replace('"', r'\"')

    if use_stmt_ids is not None and use_insn_ids is not None:
        raise TypeError("may not specify both use_stmt_ids and use_insn_ids")

    if use_insn_ids is not None:
        use_stmt_ids = use_insn_ids
        from warnings import warn
        warn("'use_insn_ids' is deprecated. Use 'use_stmt_ids' instead.",
                DeprecationWarning, stacklevel=2)

    def get_node_attrs(stmt):
        if use_stmt_ids:
            stmt_label = stmt.id
            tooltip = statement_stringifier(stmt)
        else:
            stmt_label = statement_stringifier(stmt)
            tooltip = stmt.id

        return f'label="{stmt_label}",shape="box",tooltip="{tooltip}"'

    lines = list(preamble_hook())
    lines.append("rankdir=BT;")
    dep_graph = {}

    # maps (oriented) edge onto annotation string
    annotation_dep_graph = {}

    for stmt in statements:
        lines.append('"{}" [{}];'.format(stmt.id, get_node_attrs(stmt)))
        for dep in stmt.depends_on:
            dep_graph.setdefault(stmt.id, set()).add(dep)

        if 0:
            for dep in stmt.then_depends_on:
                annotation_dep_graph[stmt.id, dep] = "then"
            for dep in stmt.else_depends_on:
                annotation_dep_graph[stmt.id, dep] = "else"

    # {{{ O(n^3) (i.e. slow) transitive reduction

    # first, compute transitive closure by fixed point iteration
    while True:
        changed_something = False

        for stmt_1 in dep_graph:
            for stmt_2 in dep_graph.get(stmt_1, set()).copy():
                for stmt_3 in dep_graph.get(stmt_2, set()).copy():
                    if stmt_3 not in dep_graph.get(stmt_1, set()):
                        changed_something = True
                        dep_graph[stmt_1].add(stmt_3)

        if not changed_something:
            break

    for stmt_1 in dep_graph:
        for stmt_2 in dep_graph.get(stmt_1, set()).copy():
            for stmt_3 in dep_graph.get(stmt_2, set()).copy():
                if stmt_3 in dep_graph.get(stmt_1, set()):
                    dep_graph[stmt_1].remove(stmt_3)

    # }}}

    for stmt_1 in dep_graph:
        for stmt_2 in dep_graph.get(stmt_1, set()):
            lines.append(f"{stmt_1} -> {stmt_2}")

    for (stmt_1, stmt_2), annot in annotation_dep_graph.items():
        lines.append(f'{stmt_2} -> {stmt_1}  [label="{annot}", style="dashed"]')

    lines.extend(additional_lines_hook())

    return "digraph code {\n%s\n}" % ("\n".join(lines))

# }}}


# {{{ graphviz / dot interactive show

def show_dot(dot_code, output_to=None):
    from warnings import warn
    warn("pymbolic.imperative.utils.show_dot is deprecated. "
         "It will stop working in July 2023. "
         "Please use pytools.graphviz.show_dot instead.",
         DeprecationWarning, stacklevel=2)

    from pytools.graphviz import show_dot
    return show_dot(dot_code, output_to)
# }}}

# vim: fdm=marker
