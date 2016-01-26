"""Instruction types"""

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


import six

from pytools import RecordWithoutPickling


# {{{ instruction classes

class Instruction(RecordWithoutPickling):
    """
    .. attribute:: depends_on

        A :class:`frozenset` of instruction ids that are reuqired to be
        executed within this execution context before this instruction can be
        executed.

    .. attribute:: id

        A string, a unique identifier for this instruction.

    .. automethod:: get_written_variables
    .. automethod:: get_read_variables
    """

    def __init__(self, **kwargs):
        id = kwargs.pop("id", None)
        if id is not None:
            id = six.moves.intern(id)

        depends_on = frozenset(kwargs.pop("depends_on", []))
        super(Instruction, self).__init__(
                                       id=id,
                                       depends_on=depends_on,
                                       **kwargs)

    def get_written_variables(self):
        """Returns a :class:`frozenset` of variables being written by this
        instruction.
        """
        return frozenset()

    def get_read_variables(self):
        """Returns a :class:`frozenset` of variables being read by this
        instruction.
        """
        return frozenset()

    def map_expressions(self, mapper, include_lhs=True):
        """Returns a new copy of *self* with all expressions
        replaced by ``mapepr(expr)`` for every
        :class:`pymbolic.primitives.Expression`
        contained in *self*.
        """
        return self

    def get_dependency_mapper(self, include_calls="descend_args"):
        from pymbolic.mapper.dependency import DependencyMapper
        return DependencyMapper(
            include_subscripts=False,
            include_lookups=False,
            include_calls=include_calls)

# }}}


# {{{ instruction with condition

class ConditionalInstruction(Instruction):
    __doc__ = Instruction.__doc__ + """
    .. attribute:: condition

       The instruction condition as a :mod:`pymbolic` expression (`True` if the
       instruction is unconditionally executed)
    """

    def __init__(self, **kwargs):
        condition = kwargs.pop("condition", True)
        super(ConditionalInstruction, self).__init__(
                condition=condition,
                **kwargs)

    def _condition_printing_suffix(self):
        if self.condition is True:
            return ""
        return " if " + str(self.condition)

    def __str__(self):
        return (super(ConditionalInstruction, self).__str__()
                + self._condition_printing_suffix())

    def get_read_variables(self):
        dep_mapper = self.get_dependency_mapper()
        return (
                super(ConditionalInstruction, self).get_read_variables()
                |
                frozenset(
                    dep.name for dep in dep_mapper(self.condition)))

# }}}


# {{{ assignment

class Assignment(Instruction):
    """
    .. attribute:: lhs
    .. attribute:: rhs
    """

    def __init__(self, lhs, rhs, **kwargs):
        super(Assignment, self).__init__(
                lhs=lhs,
                rhs=rhs,
                **kwargs)

    def get_written_variables(self):
        from pymbolic.primitives import Variable, Subscript
        if isinstance(self.lhs, Variable):
            return frozenset([self.lhs.name])
        elif isinstance(self.lhs, Subscript):
            assert isinstance(self.lhs.aggregate, Variable)
            return frozenset([self.lhs.aggregate.name])
        else:
            raise TypeError("unexpected type of LHS")

    def get_read_variables(self):
        result = super(Assignment, self).get_read_variables()
        get_deps = self.get_dependency_mapper()

        def get_vars(expr):
            return frozenset(dep.name for dep in get_deps(self.rhs))

        result = get_vars(self.rhs) | get_vars(self.lhs)

        return result

    def map_expressions(self, mapper, include_lhs=True):
        return (super(Assignment, self)
                .map_expressions(mapper, include_lhs=include_lhs)
                .copy(
                    lhs=mapper(self.lhs) if include_lhs else self.lhs,
                    rhs=mapper(self.rhs)))

    def __str__(self):
        result = "{assignee} <- {expr}".format(
            assignee=str(self.lhs),
            expr=str(self.rhs),)

        return result

# }}}


# {{{ conditional assignment

class ConditionalAssignment(ConditionalInstruction, Assignment):
    """
    .. attribute:: assignee
    .. attribute:: assignee_subscript

        The subscript in :attr:`assignee` which is being assigned.
        A tuple, which may be empty, to indicate 'no subscript'.

    .. attribute:: expression
    .. attribute:: loops

        A list of triples *(identifier, start, end)* that the assignment
        should be carried out inside of these loops.
        No ordering of loop iterations is implied.
        The loops will typically be nested outer-to-inner, but a target
        may validly use any order it likes.

    """

    def map_expressions(self, mapper, include_lhs=True):
        return (super(ConditionalAssignment, self)
                .map_expressions(mapper, include_lhs=include_lhs)
                .copy(condition=mapper(self.condition)))

# }}}


# {{{ nop

class Nop(Instruction):
    def __str__(self):
        return 'nop'

# }}}


# vim: foldmethod=marker
