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


# {{{ fuse instruction streams

def fuse_instruction_streams_with_unique_ids(instructions_a, instructions_b):
    new_instructions = instructions_a[:]
    from pytools import UniqueNameGenerator
    insn_id_gen = UniqueNameGenerator(
            set([insna.id for insna in new_instructions]))

    b_unique_instructions = []
    old_b_id_to_new_b_id = {}
    for insnb in instructions_b:
        old_id = insnb.id
        new_id = insn_id_gen(old_id)
        old_b_id_to_new_b_id[old_id] = new_id

        b_unique_instructions.append(
                insnb.copy(id=new_id))

    for insnb in b_unique_instructions:
        new_instructions.append(
                insnb.copy(
                    depends_on=frozenset(
                        old_b_id_to_new_b_id[dep_id]
                        for dep_id in insnb.depends_on)))

    return new_instructions, old_b_id_to_new_b_id

# }}}


# vim: foldmethod=marker
