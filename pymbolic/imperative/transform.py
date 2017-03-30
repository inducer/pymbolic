"""Imperative program representation: transformations"""

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


# {{{ fuse overlapping instruction streams

def fuse_instruction_streams_with_overlapping_ids(instructions_a, instructions_b,
        allowed_duplicates=[]):
    id_a = set([insna.id for insna in instructions_a])
    # filter b instructions
    uniques_b = [x for x in instructions_b
                    if x.id in id_a
                    and x.id not in allowed_duplicates]

    return fuse_instruction_streams_with_unique_ids(instructions_a, uniques_b,
        allow_b_depend_on_a=True)

# }}}


# {{{ fuse instruction streams

def fuse_instruction_streams_with_unique_ids(instructions_a, instructions_b,
        allow_b_depend_on_a=False):
    new_instructions = list(instructions_a)
    from pytools import UniqueNameGenerator
    insn_id_gen = UniqueNameGenerator(
            set([insna.id for insna in new_instructions]))

    a_ids = set([insna.id for insna in instructions_a])
    b_unique_instructions = []
    old_b_id_to_new_b_id = {}
    for insnb in instructions_b:
        old_id = insnb.id
        new_id = insn_id_gen(old_id)
        old_b_id_to_new_b_id[old_id] = new_id

        b_unique_instructions.append(
                insnb.copy(id=new_id))

    for insnb in b_unique_instructions:
        # Now we must update the dependencies in `instructions_b` to
        # the new b_id's.
        # If allow_b_depend_on_a is True, `insnb` is allowed to depend on
        # instructions in `instructions_a`
        b_deps = set()
        for dep_id in insnb.depends_on:
            # First, see if the dependency is in the updated `instructions_b`
            # ids.
            new_dep_id = old_b_id_to_new_b_id.get(dep_id)
            # Next, if allow_b_depend_on_a, check the a_ids
            if allow_b_depend_on_a and new_dep_id is None:
                new_dep_id = dep_id if dep_id in a_ids else None
            # If the dependency is not found in `instructions_a` or the updated
            # `instructions_b`, raise an AssertionError.
            assert new_dep_id is not None, ('Instruction {0} in stream b '
                'missing dependency {1}'.format(insnb.id, dep_id))
            b_deps.add(new_dep_id)

        new_instructions.append(
                insnb.copy(depends_on=frozenset(b_deps)))

    return new_instructions, old_b_id_to_new_b_id

# }}}


# {{{ disambiguate_identifiers

def disambiguate_identifiers(instructions_a, instructions_b,
        should_disambiguate_name=None):
    if should_disambiguate_name is None:
        def should_disambiguate_name(name):
            return True

    from pymbolic.imperative.analysis import get_all_used_identifiers

    id_a = get_all_used_identifiers(instructions_a)
    id_b = get_all_used_identifiers(instructions_b)

    from pytools import UniqueNameGenerator
    vng = UniqueNameGenerator(id_a | id_b)

    from pymbolic import var
    subst_b = {}
    for clash in id_a & id_b:
        if should_disambiguate_name(clash):
            unclash = vng(clash)
            subst_b[clash] = var(unclash)

    from pymbolic.mapper.substitutor import (
            make_subst_func, SubstitutionMapper)
    subst_map = SubstitutionMapper(make_subst_func(subst_b))

    instructions_b = [
            insn.map_expressions(subst_map) for insn in instructions_b]

    return instructions_b, subst_b

# }}}


# {{{ disambiguate_and_fuse

def disambiguate_and_fuse(instructions_a, instructions_b,
        should_disambiguate_name=None):
    instructions_b, subst_b = disambiguate_identifiers(
            instructions_a, instructions_b,
            should_disambiguate_name)

    fused, old_b_id_to_new_b_id = \
            fuse_instruction_streams_with_unique_ids(
                    instructions_a, instructions_b)

    return fused, subst_b, old_b_id_to_new_b_id

# }}}


# vim: foldmethod=marker
