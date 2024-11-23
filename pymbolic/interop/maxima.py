from __future__ import annotations


__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

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

__doc__ = """

.. autoclass:: MaximaStringifyMapper
.. autoclass:: MaximaParser
.. autoclass:: MaximaKernel

.. autofunction:: eval_expr_with_setup
.. autofunction:: diff

"""

# Inspired by similar code in Sage at:
# https://github.com/sagemath/sage/blob/master/src/sage/interfaces/maxima.py

import re
from sys import intern
from typing import ClassVar

import numpy as np

import pytools

from pymbolic.mapper.stringifier import StringifyMapper
from pymbolic.parser import FinalizedTuple, LexTable, Parser as ParserBase


IN_PROMPT_RE = re.compile(br"\(%i([0-9]+)\) ")
OUT_PROMPT_RE = re.compile(br"\(%o([0-9]+)\) ")
ERROR_PROMPT_RE = re.compile(
    br"(Principal Value|debugmode|incorrect syntax|Maxima encountered a Lisp error)")
ASK_RE = re.compile(
        br"(zero or nonzero|an integer|positive, negative, or zero|"
        br"positive or negative|positive or zero)")
MULTI_WHITESPACE = re.compile(br"[ \r\n\t]+")


class MaximaError(RuntimeError):
    pass


# {{{ stringifier

class MaximaStringifyMapper(StringifyMapper):
    def map_power(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_POWER
        return self.parenthesize_if_needed(
                self.format("%s^%s",
                    self.rec(expr.base, PREC_POWER),
                    self.rec(expr.exponent, PREC_POWER)),
                enclosing_prec, PREC_POWER)

    def map_constant(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_SUM
        if isinstance(expr, complex):
            result = f"{expr.real!r} + {expr.imag!r}*%i"
        else:
            result = repr(expr)

        if not (result.startswith("(") and result.endswith(")")) \
                and ("-" in result or "+" in result) \
                and (enclosing_prec > PREC_SUM):
            return self.parenthesize(result)
        else:
            return result


# }}}


# {{{ parser

class MaximaParser(ParserBase):
    power_sym = intern("power")
    imag_unit = intern("imag_unit")
    euler_number = intern("euler_number")

    lex_table: ClassVar[LexTable] = [
            (power_sym, pytools.lex.RE(r"\^")),
            (imag_unit, pytools.lex.RE(r"%i")),
            (euler_number, pytools.lex.RE(r"%e")),
            *ParserBase.lex_table
            ]

    def parse_prefix(self, pstate):
        pstate.expect_not_end()

        from pymbolic.parser import _closebracket, _openbracket
        if pstate.is_next(_openbracket):
            pstate.advance()
            left_exp = self.parse_expression(pstate)
            pstate.expect(_closebracket)
            pstate.advance()
            if isinstance(left_exp, tuple):
                left_exp = FinalizedTuple(left_exp)
        else:
            left_exp = super().parse_prefix(pstate)

        return left_exp

    def parse_terminal(self, pstate):
        import pymbolic.primitives as primitives

        next_tag = pstate.next_tag()
        import pymbolic.parser as p
        if next_tag is p._int:
            return int(pstate.next_str_and_advance())
        elif next_tag is p._float:
            return float(pstate.next_str_and_advance())
        elif next_tag is self.imag_unit:
            pstate.advance()
            return 1j
        elif next_tag is self.euler_number:
            pstate.advance()
            return np.e
        elif next_tag is p._identifier:
            return primitives.Variable(pstate.next_str_and_advance())
        else:
            pstate.expected("terminal")

    def parse_postfix(self, pstate, min_precedence, left_exp):
        import pymbolic.parser as p
        import pymbolic.primitives as primitives

        did_something = False

        next_tag = pstate.next_tag()

        if next_tag is p._openpar and p._PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect_not_end()
            if next_tag is p._closepar:
                pstate.advance()
                left_exp = primitives.Call(left_exp, ())
            else:
                args = self.parse_expression(pstate)
                if not isinstance(args, tuple):
                    args = (args,)

                pstate.expect(p._closepar)
                pstate.advance()

                if left_exp == primitives.Variable("matrix"):
                    left_exp = np.array([list(row) for row in args])
                else:
                    left_exp = primitives.Call(left_exp, args)

            did_something = True
        elif next_tag is p._openbracket and p._PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect_not_end()
            left_exp = primitives.Subscript(left_exp, self.parse_expression(pstate))
            pstate.expect(p._closebracket)
            pstate.advance()
            did_something = True
        elif next_tag is p._dot and p._PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect(p._identifier)
            left_exp = primitives.Lookup(left_exp, pstate.next_str())
            pstate.advance()
            did_something = True
        elif next_tag is p._plus and p._PREC_PLUS > min_precedence:
            pstate.advance()
            left_exp += self.parse_expression(pstate, p._PREC_PLUS)
            did_something = True
        elif next_tag is p._minus and p._PREC_PLUS > min_precedence:
            pstate.advance()
            left_exp -= self.parse_expression(pstate, p._PREC_PLUS)
            did_something = True
        elif next_tag is p._times and p._PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp *= self.parse_expression(pstate, p._PREC_TIMES)
            did_something = True
        elif next_tag is p._over and p._PREC_TIMES > min_precedence:
            pstate.advance()
            from pymbolic.primitives import Quotient
            left_exp = Quotient(
                    left_exp, self.parse_expression(pstate, p._PREC_TIMES))
            did_something = True
        elif next_tag is self.power_sym and p._PREC_POWER > min_precedence:
            pstate.advance()
            exponent = self.parse_expression(pstate, p._PREC_POWER)
            if left_exp == np.e:
                from pymbolic.primitives import Call, Variable
                left_exp = Call(Variable("exp"), (exponent,))
            else:
                left_exp **= exponent
            did_something = True
        elif next_tag is p._comma and p._PREC_COMMA > min_precedence:
            # The precedence makes the comma left-associative.

            pstate.advance()
            if pstate.is_at_end() or pstate.next_tag() is p._closepar:
                left_exp = (left_exp,)
            else:
                new_el = self.parse_expression(pstate, p._PREC_COMMA)
                if isinstance(left_exp, tuple) \
                        and not isinstance(left_exp, FinalizedTuple):
                    left_exp = (*left_exp, new_el)
                else:
                    left_exp = (left_exp, new_el)

            did_something = True

        return left_exp, did_something

# }}}


# {{{ pexpect-based driver

_DEBUG = False


def set_debug(level):
    global _DEBUG
    _DEBUG = level


def _strify_assignments_and_expr(assignments, expr):
    strify = MaximaStringifyMapper()

    if isinstance(expr, str):
        expr_str = expr
    else:
        expr_str = strify(expr)

    def make_setup(assignment):
        if isinstance(assignment, str):
            return assignment
        if isinstance(assignment, tuple):
            name, value = assignment
            return "{}: {}".format(name, strify(value))
        else:
            return strify(assignment)

    return tuple(make_setup(assignment) for assignment in assignments), expr_str


class MaximaKernel:
    """
    .. automethod:: restart
    .. automethod:: shutdown
    .. automethod:: reset
    .. automethod:: exec_str
    .. automethod:: eval_str
    .. automethod:: eval_expr
    """

    def __init__(self, executable="maxima", timeout=30):
        self.executable = executable
        self.timeout = timeout

        self._initialize()

    # {{{ internal

    def _initialize(self):

        PEXPECT_SHELL = "bash"  # noqa

        PRE_MAXIMA_COMMANDS = (  # noqa
            # Makes long line inputs possible.
            ("stty -icanon",)
        )

        import pexpect
        self.child = pexpect.spawn(PEXPECT_SHELL, timeout=self.timeout, echo=False)
        for command in PRE_MAXIMA_COMMANDS:
            self.child.sendline(command)

        # {{{ check for maxima command

        self.child.sendline(
            f'hash "{self.executable}"; echo $?')

        hash_output = self.child.expect(["0\r\n", "1\r\n"])
        if hash_output != 0:
            raise RuntimeError(
                f"maxima executable '{self.executable}' not found")

        # }}}

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".lisp") as maxima_init_f:

            # https://sourceforge.net/p/maxima/bugs/3909/
            # FIXME assumes gcl in use
            maxima_init_f.write(
                    b"(if (find :editline *features*) (si::readline-off))")
            maxima_init_f.flush()

            self.child.sendline(" ".join(
                    ['"' + self.executable + '"',
                        "-p", maxima_init_f.name,
                        "--disable-readline",
                        "-q"]))

            self.current_prompt = 0
            self._expect_prompt(IN_PROMPT_RE)

        self.exec_str("display2d:false")
        self.exec_str("keepfloat:true")
        self.exec_str("linel:16384")

    def _expect_prompt(self, prompt_re, enforce_prompt_numbering=True):
        if prompt_re is IN_PROMPT_RE:
            self.current_prompt += 1

        which = self.child.expect([prompt_re, ERROR_PROMPT_RE, ASK_RE])
        if which == 0:
            if enforce_prompt_numbering:
                assert int(self.child.match.group(1)) == self.current_prompt, (
                        "found prompt: {}, expected: {}".format(
                            self.child.match.group(1).decode(),
                            self.current_prompt))
            else:
                self.current_prompt = int(self.child.match.group(1).decode())

            return

        if which == 1:
            txt = self.child.before+self.child.after+self.child.readline()
            txt = txt.decode()
            self.restart()
            raise MaximaError(
                    "maxima encountered an error and had to be restarted:"
                    "\n{}\n{}\n{}".format(75*"-", txt.rstrip("\n"), 75*"-"))
        elif which == 2:
            txt = self.child.before+self.child.after+self.child.readline()
            txt = txt.decode()
            self.restart()
            raise MaximaError(
                    "maxima asked a question and had to be restarted:"
                    "\n{}\n{}\n{}".format(75*"-", txt.rstrip("\n"), 75*"-"))
        else:
            self.restart()
            raise MaximaError("unexpected output from maxima, restarted")

    # }}}

    # {{{ execution control

    def restart(self):
        # https://github.com/pexpect/pexpect/issues/462
        # caused issues like
        # https://gitlab.tiker.net/inducer/pymbolic/-/jobs/50932
        self.child.delayafterclose = 5
        self.child.ptyproc.delayafterclose = 5

        self.child.close(force=True)
        self._initialize()

    def shutdown(self):
        self._sendline("quit();")
        # Exit shell
        self._sendline("exit")
        from pexpect import EOF
        self.child.expect(EOF)
        self.child.wait()

    # }}}

    # {{{ string interface

    def _check_debug(self):
        if _DEBUG & 4:
            import sys
            self.child.logfile = sys.stdout

    def _sendline(self, line):
        self._check_debug()
        self.child.sendline(line)

    def exec_str(self, s, enforce_prompt_numbering=True):
        cmd = s+";"
        if _DEBUG & 1:
            print("[MAXIMA INPUT]", cmd)

        self._sendline(s+";")
        self._expect_prompt(
                IN_PROMPT_RE,
                enforce_prompt_numbering=enforce_prompt_numbering)

    def eval_str(self, s, enforce_prompt_numbering=True):
        self._check_debug()

        cmd = s+";"
        if _DEBUG & 1:
            print("[MAXIMA INPUT]", cmd)

        self._sendline(cmd)

        self._expect_prompt(OUT_PROMPT_RE,
                enforce_prompt_numbering=enforce_prompt_numbering)
        self._expect_prompt(IN_PROMPT_RE)

        result, _ = MULTI_WHITESPACE.subn(b" ", self.child.before)

        if _DEBUG & 1:
            print("[MAXIMA RESPONSE]", result)
        return result.decode()

    def reset(self):
        self.current_prompt = 0
        self.exec_str("kill(all)")

    def clean_eval_str_with_setup(self, setup_lines, s):
        self.reset()
        for line in setup_lines:
            self.exec_str(line)

        return self.eval_str(s)

    # }}}

    # {{{ expression interface

    def eval_expr(self, expr):
        input_str = MaximaStringifyMapper()(expr)
        result_str = self.eval_str(input_str)
        parsed = MaximaParser()(result_str)
        if _DEBUG & 2:
            print("[MAXIMA PARSED]", parsed)
        return parsed

    def clean_eval_expr_with_setup(self, assignments, expr):
        result_str = self.clean_eval_str_with_setup(
                *_strify_assignments_and_expr(assignments, expr))

        parsed = MaximaParser()(result_str)
        if _DEBUG & 2:
            print("[MAXIMA PARSED  ]", parsed)
        return parsed

    # }}}

# }}}


# {{{ global kernel instance

_kernel_instance = None


@pytools.memoize
def _cached_eval_expr_with_setup(assignments, expr):
    global _kernel_instance
    if _kernel_instance is None:
        _kernel_instance = MaximaKernel()

    return _kernel_instance.clean_eval_expr_with_setup(assignments, expr)


def eval_expr_with_setup(assignments, expr):
    assignments, expr = _strify_assignments_and_expr(assignments, expr)
    return _cached_eval_expr_with_setup(assignments, expr)

# }}}


# {{{ "classic" CAS functionality

def diff(expr, var, count=1, assignments=()):
    from pymbolic import var as sym
    if isinstance(var, str):
        var = sym(var)
    return eval_expr_with_setup(assignments, sym("diff")(expr, var, count))

# }}}


# vim: fdm=marker
