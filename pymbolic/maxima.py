# Inspired by similar code in Sage at:
# http://trac.sagemath.org/sage_trac/browser/sage/interfaces/maxima.py

import pexpect
import re
import pytools

from pymbolic.mapper.stringifier import StringifyMapper
from pymbolic.parser import Parser as ParserBase




IN_PROMPT_RE = re.compile(r"\(%i([0-9]+)\) ")
OUT_PROMPT_RE = re.compile(r"\(%o([0-9]+)\) ")
ERROR_PROMPT_RE = re.compile(r"(Principal Value|debugmode|incorrect syntax|Maxima encountered a Lisp error)")
ASK_RE = re.compile(r"(zero or nonzero|an integer|positive, negative, or zero|"
        "positive or negative|positive or zero)")
MULTI_WHITESPACE = re.compile(r"[ \r\n\t]+")




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
            result = "%r + %r*%%i" % (expr.real, expr.imag)
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

    lex_table = [
            (power_sym, pytools.lex.RE(r"\^")),
            (imag_unit, pytools.lex.RE(r"%i")),
            ] + ParserBase.lex_table

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
        elif next_tag is p._identifier:
            return primitives.Variable(pstate.next_str_and_advance())
        else:
            pstate.expected("terminal")

    def parse_postfix(self, pstate, min_precedence, left_exp):
        import pymbolic.primitives as primitives
        import pymbolic.parser as p

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
                left_exp = primitives.Call(left_exp, args)
                pstate.expect(p._closepar)
                pstate.advance()
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
            left_exp = Quotient(left_exp, self.parse_expression(pstate, p._PREC_TIMES))
            did_something = True
        elif next_tag is self.power_sym and p._PREC_POWER > min_precedence:
            pstate.advance()
            left_exp **= self.parse_expression(pstate, p._PREC_POWER)
            did_something = True

        return left_exp, did_something

# }}}




# {{{ pexpect-based driver

class MaximaKernel:
    def __init__(self, executable="maxima", timeout=30):
        self.executable = executable
        self.timeout = timeout

        self._initialize()

    # {{{ internal

    def _initialize(self):
        self.child = pexpect.spawn(self.executable,
                ["--disable-readline", "-q"],
                timeout=self.timeout)
        #import sys
        #self.child.logfile = sys.stdout
        self.current_prompt = 0
        self._expect_prompt(IN_PROMPT_RE)

        self.exec_str("display2d:false")
        self.exec_str("keepfloat:true")

    def _expect_prompt(self, prompt_re):
        if prompt_re is IN_PROMPT_RE:
            self.current_prompt += 1

        which = self.child.expect([prompt_re, ERROR_PROMPT_RE, ASK_RE])
        if which == 0:
            assert int(self.child.match.group(1)) == self.current_prompt
            return
        if which == 1:
            txt = self.child.before+self.child.after+self.child.readline()
            self.restart()
            raise MaximaError("maxima encountered an error and had to be restarted:\n%s\n%s\n%s"
                    % (75*"-", txt.rstrip("\n"), 75*"-"))
        elif which == 2:
            txt = self.child.before+self.child.after+self.child.readline()
            self.restart()
            raise MaximaError("maxima asked a question and had to be restarted:\n%s\n%s\n%s"
                    % (75*"-", txt.rstrip("\n"), 75*"-"))
        else:
            self.restart()
            raise MaximaError("unexpected output from maxima, restarted")

    # }}}

    # {{{ execution control

    def restart(self):
        from signal import SIGKILL
        self.child.kill(SIGKILL)
        self._initialize()

    def shutdown(self):
        self.child.sendline("quit();")
        self.child.wait()

    # }}}

    # {{{ string interface

    def exec_str(self, s):
        self.child.sendline(s+";")
        self._expect_prompt(IN_PROMPT_RE)

    def eval_str(self, s):
        cmd = s+";"
        self.child.sendline(cmd)
        s_echo = self.child.readline()
        assert s_echo.strip() == cmd.strip()

        self._expect_prompt(OUT_PROMPT_RE)
        self._expect_prompt(IN_PROMPT_RE)

        result, _ = MULTI_WHITESPACE.subn(" ", self.child.before)
        return result

    def reset(self):
        self.current_prompt = 0
        self.exec_str("kill(all)")

    def clean_eval_str_with_setup(self, setup_lines, s):
        self.reset()
        for l in setup_lines:
            self.exec_str(l)

        return self.eval_str(s)

    # }}}

    # {{{ expression interface

    def eval_expr(self, expr):
        input_str = MaximaStringifyMapper()(expr)
        result_str = self.eval_str(input_str)
        return MaximaParser()(result_str)

    def clean_eval_expr_with_setup(self, assignments, expr):
        strify = MaximaStringifyMapper()

        if isinstance(expr, str):
            input_str = expr
        else:
            input_str = strify(expr)

        def make_setup(assignment):
            if isinstance(assignment, str):
                return assignment
            else:
                name, value = assignment
                return"%s: %s" % (name, strify(value))

        result_str = self.clean_eval_str_with_setup(
                [make_setup(assignment) for assignment in assignments],
                input_str)
        return MaximaParser()(result_str)

    # }}}

# }}}

# vim: fdm=marker
