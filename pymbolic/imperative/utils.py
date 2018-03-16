from __future__ import division, with_statement

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


import six
import logging

logger = logging.getLogger(__name__)


# {{{ graphviz / dot export

def _default_preamble_hook():
    # Sets default attributes for nodes and edges.
    yield "node [shape=\"box\"];"
    yield "edge [dir=\"back\"];"


def get_dot_dependency_graph(
        statements,  use_stmt_ids=None,
        preamble_hook=_default_preamble_hook,
        additional_lines_hook=list,

        # deprecated
        use_insn_ids=None,):
    """Return a string in the `dot <http://graphviz.org/>`_ language depicting
    dependencies among kernel statements.

    :arg preamble_hook: A function that returns an iterable of lines
        to add at the beginning of the graph
    :arg additional_lines_hook: A function that returns an iterable
        of lines to add at the end of the graph
    """

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
            tooltip = str(stmt)
        else:
            stmt_label = str(stmt)
            tooltip = stmt.id

        return "label=\"%s\",shape=\"box\",tooltip=\"%s\"" % (
                repr(stmt_label)[1:-1],
                repr(tooltip)[1:-1],
                )

    lines = list(preamble_hook())
    dep_graph = {}

    # maps (oriented) edge onto annotation string
    annotation_dep_graph = {}

    for stmt in statements:
        lines.append("\"%s\" [%s];" % (stmt.id, get_node_attrs(stmt)))
        for dep in stmt.depends_on:
            dep_graph.setdefault(stmt.id, set()).add(dep)

        if 0:
            for dep in stmt.then_depends_on:
                annotation_dep_graph[(stmt.id, dep)] = "then"
            for dep in stmt.else_depends_on:
                annotation_dep_graph[(stmt.id, dep)] = "else"

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
            lines.append("%s -> %s" % (stmt_2, stmt_1))

    for (stmt_1, stmt_2), annot in six.iteritems(annotation_dep_graph):
            lines.append(
                    "%s -> %s  [label=\"%s\",style=\"dashed\"]"
                    % (stmt_2, stmt_1, annot))

    lines.extend(additional_lines_hook())

    return "digraph code {\n%s\n}" % (
            "\n".join(lines)
            )

# }}}


# {{{ graphviz / dot interactive show

def show_dot(dot_code):
    """Show the graph represented by *dot_code* in a browser.
    Can be called on the result of :func:`get_dot_dependency_graph`.
    """

    from tempfile import mkdtemp
    temp_dir = mkdtemp(prefix="tmp_dagrt_dot")

    dot_file_name = "code.dot"

    from os.path import join
    with open(join(temp_dir, dot_file_name), "w") as dotf:
        dotf.write(dot_code)

    svg_file_name = "code.svg"
    from subprocess import check_call
    check_call(["dot", "-Tsvg", "-o", svg_file_name, dot_file_name],
            cwd=temp_dir)

    full_svg_file_name = join(temp_dir, svg_file_name)
    logger.info("show_dot_dependency_graph: svg written to '%s'"
            % full_svg_file_name)

    from webbrowser import open as browser_open
    browser_open("file://" + full_svg_file_name)

# }}}

# vim: fdm=marker
