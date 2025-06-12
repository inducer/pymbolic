"""Imperative program representation: transformations"""
from __future__ import annotations


__copyright__ = "Copyright (C) 2015 Matt Wala, Andreas Kloeckner"

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


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pymbolic.imperative.statement import (
        BasicStatementLikeT,
        StatementLike,
        StatementLikeT,
    )
    from pymbolic.primitives import Variable


# {{{ fuse statement streams

def fuse_statement_streams_with_unique_ids(
            statements_a: Sequence[BasicStatementLikeT],
            statements_b: Sequence[BasicStatementLikeT]
        ) -> tuple[list[BasicStatementLikeT], dict[str, str]]:
    new_statements = list(statements_a)
    from pytools import UniqueNameGenerator
    stmt_id_gen = UniqueNameGenerator(
            {stmta.id for stmta in new_statements})

    b_unique_statements: list[BasicStatementLikeT] = []
    old_b_id_to_new_b_id: dict[str, str] = {}
    for stmtb in statements_b:
        old_id = stmtb.id
        new_id = stmt_id_gen(old_id)
        old_b_id_to_new_b_id[old_id] = new_id

        b_unique_statements.append(
                stmtb.copy(id=new_id))

    for stmtb in b_unique_statements:
        new_statements.append(
                stmtb.copy(
                    depends_on=frozenset(
                        old_b_id_to_new_b_id[dep_id]
                        for dep_id in stmtb.depends_on)))

    return new_statements, old_b_id_to_new_b_id


def fuse_instruction_streams_with_unique_ids(
            insns_a: Sequence[StatementLikeT],
            insns_b: Sequence[StatementLikeT]
        ):
    from warnings import warn
    warn("fuse_instruction_streams_with_unique_ids has been renamed to "
            "fuse_statement_streams_with_unique_ids", DeprecationWarning,
            stacklevel=2)

    return fuse_statement_streams_with_unique_ids(insns_a, insns_b)

# }}}


# {{{ disambiguate_identifiers

def disambiguate_identifiers(
            statements_a: Sequence[StatementLike],
            statements_b: Sequence[StatementLike],
            should_disambiguate_name: Callable[[str], bool] | None = None,
        ):
    if should_disambiguate_name is None:
        should_disambiguate_name = lambda name: True  # noqa: E731

    from pymbolic.imperative.analysis import get_all_used_identifiers

    id_a = get_all_used_identifiers(statements_a)
    id_b = get_all_used_identifiers(statements_b)

    from pytools import UniqueNameGenerator
    vng = UniqueNameGenerator(id_a | id_b)

    from pymbolic import var
    subst_b: dict[str, Variable] = {}
    for clash in id_a & id_b:
        if should_disambiguate_name(clash):
            unclash = vng(clash)
            subst_b[clash] = var(unclash)

    from pymbolic.mapper.substitutor import SubstitutionMapper, make_subst_func
    subst_map = SubstitutionMapper(make_subst_func(subst_b))

    statements_b = [
            stmt.map_expressions(subst_map) for stmt in statements_b]

    return statements_b, subst_b

# }}}


# {{{ disambiguate_and_fuse

def disambiguate_and_fuse(
            statements_a: Sequence[StatementLike],
            statements_b: Sequence[StatementLike],
            should_disambiguate_name: Callable[[str], bool] | None = None,
        ):
    statements_b, subst_b = disambiguate_identifiers(
            statements_a, statements_b,
            should_disambiguate_name)

    fused, old_b_id_to_new_b_id = \
            fuse_statement_streams_with_unique_ids(
                    statements_a, statements_b)

    return fused, subst_b, old_b_id_to_new_b_id

# }}}


# vim: foldmethod=marker
