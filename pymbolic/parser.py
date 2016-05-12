from __future__ import division, absolute_import

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

import pytools.lex
from six.moves import intern

_imaginary = intern("imaginary")
_float = intern("float")
_int = intern("int")
_power = intern("exp")
_plus = intern("plus")
_minus = intern("minus")
_times = intern("times")
_floordiv = intern("floordiv")
_over = intern("over")
_modulo = intern("modulo")
_openpar = intern("openpar")
_closepar = intern("closepar")
_openbracket = intern("openbracket")
_closebracket = intern("closebracket")
_identifier = intern("identifier")
_whitespace = intern("whitespace")
_comma = intern("comma")
_dot = intern("dot")
_colon = intern("colon")

_assign = intern("assign")

_equal = intern("equal")
_notequal = intern("notequal")
_less = intern("less")
_lessequal = intern("lessequal")
_greater = intern("greater")
_greaterequal = intern("greaterequal")

_leftshift = intern("leftshift")
_rightshift = intern("rightshift")

_and = intern("and")
_or = intern("or")
_not = intern("not")

_bitwiseand = intern("bitwiseand")
_bitwiseor = intern("bitwiseor")
_bitwisexor = intern("bitwisexor")
_bitwisenot = intern("bitwisenot")

_PREC_COMMA = 5  # must be > 1 (1 is used by fortran-to-cl)
_PREC_SLICE = 10
_PREC_LOGICAL_OR = 80
_PREC_LOGICAL_AND = 90

_PREC_BITWISE_OR = 120
_PREC_BITWISE_XOR = 120
_PREC_BITWISE_AND = 130

_PREC_COMPARISON = 200
_PREC_SHIFT = 205
_PREC_PLUS = 210
_PREC_TIMES = 220
_PREC_POWER = 230
_PREC_UNARY = 240
_PREC_CALL = 250


def _join_to_slice(left, right):
    from pymbolic.primitives import Slice
    if isinstance(right, Slice):
        return Slice((left,) + right.children)
    else:
        return Slice((left, right))


class FinalizedTuple(tuple):
    """A tuple that may not have elements appended to it, because it was
    terminated by a close-paren.
    """


class Parser(object):
    lex_table = [
            (_equal, pytools.lex.RE(r"==")),
            (_notequal, pytools.lex.RE(r"!=")),
            (_equal, pytools.lex.RE(r"==")),

            (_leftshift, pytools.lex.RE(r"\<\<")),
            (_rightshift, pytools.lex.RE(r"\>\>")),

            (_lessequal, pytools.lex.RE(r"\<=")),
            (_greaterequal, pytools.lex.RE(r"\>=")),
            # must be before
            (_less, pytools.lex.RE(r"\<")),
            (_greater, pytools.lex.RE(r"\>")),

            (_assign, pytools.lex.RE(r"=")),

            (_and, pytools.lex.RE(r"and\b")),
            (_or, pytools.lex.RE(r"or\b")),
            (_not, pytools.lex.RE(r"not\b")),

            (_imaginary, (_float, pytools.lex.RE("j"))),
            (_float, ("|",
                # has digits before the dot (after optional)
                pytools.lex.RE(
                    r"[0-9]+\.[0-9]*([eEdD][+-]?[0-9]+)?([a-zA-Z]*)"),
                pytools.lex.RE(
                    r"[0-9]+(\.[0-9]*)?[eEdD][+-]?[0-9]+([a-zA-Z]*)\b"),
                # has digits after the dot (before optional)
                pytools.lex.RE(
                    r"[0-9]*\.[0-9]+([eEdD][+-]?[0-9]+)?([a-zA-Z]*)"),
                pytools.lex.RE(
                    r"[0-9]*\.[0-9]+[eEdD][+-]?[0-9]+([a-zA-Z]*)\b"),
                # has a letter tag
                pytools.lex.RE(r"[0-9]+([a-zA-Z]+)"),
                )),
            (_int, pytools.lex.RE(r"[0-9]+")),

            (_plus, pytools.lex.RE(r"\+")),
            (_minus, pytools.lex.RE(r"-")),
            (_power, pytools.lex.RE(r"\*\*")),
            (_times, pytools.lex.RE(r"\*")),
            (_floordiv, pytools.lex.RE(r"//")),
            (_over, pytools.lex.RE(r"/")),
            (_modulo, pytools.lex.RE(r"%")),

            (_bitwiseand, pytools.lex.RE(r"\&")),
            (_bitwiseor, pytools.lex.RE(r"\|")),
            (_bitwisenot, pytools.lex.RE(r"\~")),
            (_bitwisexor, pytools.lex.RE(r"\^")),

            (_openpar, pytools.lex.RE(r"\(")),
            (_closepar, pytools.lex.RE(r"\)")),
            (_openbracket, pytools.lex.RE(r"\[")),
            (_closebracket, pytools.lex.RE(r"\]")),
            (_identifier, pytools.lex.RE(r"[@$a-z_A-Z_][@$a-zA-Z_0-9]*")),
            (_whitespace, pytools.lex.RE("[ \n\t]*")),
            (_comma, pytools.lex.RE(",")),
            (_dot, pytools.lex.RE(r"\.")),
            (_colon, pytools.lex.RE(r"\:")),
            ]

    _COMP_TABLE = {
            _greater: ">",
            _greaterequal: ">=",
            _less: "<",
            _lessequal: "<=",
            _equal: "==",
            _notequal: "!=",
            }

    def parse_float(self, s):
        return float(s.replace("d", "e").replace("D", "e"))

    def parse_terminal(self, pstate):
        import pymbolic.primitives as primitives

        next_tag = pstate.next_tag()
        if next_tag is _int:
            return int(pstate.next_str_and_advance())
        elif next_tag is _float:
            return self.parse_float(pstate.next_str_and_advance())
        elif next_tag is _imaginary:
            return complex(pstate.next_str_and_advance())
        elif next_tag is _identifier:
            return primitives.Variable(pstate.next_str_and_advance())
        else:
            pstate.expected("terminal")

    def parse_prefix(self, pstate):
        import pymbolic.primitives as primitives
        pstate.expect_not_end()

        if pstate.is_next(_colon):
            pstate.advance()

            expr_pstate = pstate.copy()
            from pytools.lex import ParseError
            try:
                next_expr = self.parse_expression(expr_pstate, _PREC_SLICE)
            except ParseError:
                # no expression follows, too bad.
                left_exp = primitives.Slice((None,))
            else:
                left_exp = _join_to_slice(None, next_expr)
                pstate.assign(expr_pstate)
        elif pstate.is_next(_times):
            pstate.advance()
            left_exp = primitives.Wildcard()
        elif pstate.is_next(_plus):
            pstate.advance()
            left_exp = self.parse_expression(pstate, _PREC_UNARY)
        elif pstate.is_next(_minus):
            pstate.advance()
            left_exp = -self.parse_expression(pstate, _PREC_UNARY)
        elif pstate.is_next(_not):
            pstate.advance()
            from pymbolic.primitives import LogicalNot
            left_exp = LogicalNot(
                    self.parse_expression(pstate, _PREC_UNARY))
        elif pstate.is_next(_bitwisenot):
            pstate.advance()
            from pymbolic.primitives import BitwiseNot
            left_exp = BitwiseNot(
                    self.parse_expression(pstate, _PREC_UNARY))
        elif pstate.is_next(_openpar):
            pstate.advance()
            left_exp = self.parse_expression(pstate)
            pstate.expect(_closepar)
            pstate.advance()
            if isinstance(left_exp, tuple):
                left_exp = FinalizedTuple(left_exp)
        else:
            left_exp = self.parse_terminal(pstate)

        return left_exp

    def parse_expression(self, pstate, min_precedence=0):
        left_exp = self.parse_prefix(pstate)

        did_something = True
        while did_something:
            did_something = False
            if pstate.is_at_end():
                return left_exp

            result = self.parse_postfix(
                    pstate, min_precedence, left_exp)
            left_exp, did_something = result

        if isinstance(left_exp, FinalizedTuple):
            return tuple(left_exp)

        return left_exp

    def parse_postfix(self, pstate, min_precedence, left_exp):
        import pymbolic.primitives as primitives

        did_something = False

        next_tag = pstate.next_tag()

        if next_tag is _openpar and _PREC_CALL > min_precedence:
            pstate.advance()
            args, kwargs = self.parse_arglist(pstate)

            if kwargs:
                left_exp = primitives.CallWithKwargs(left_exp, args, kwargs)
            else:
                left_exp = primitives.Call(left_exp, args)

            did_something = True
        elif next_tag is _openbracket and _PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect_not_end()
            left_exp = primitives.Subscript(left_exp, self.parse_expression(pstate))
            pstate.expect(_closebracket)
            pstate.advance()
            did_something = True
        elif next_tag is _dot and _PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect(_identifier)
            left_exp = primitives.Lookup(left_exp, pstate.next_str())
            pstate.advance()
            did_something = True
        elif next_tag is _plus and _PREC_PLUS > min_precedence:
            pstate.advance()
            left_exp += self.parse_expression(pstate, _PREC_PLUS)
            did_something = True
        elif next_tag is _minus and _PREC_PLUS > min_precedence:
            pstate.advance()
            left_exp -= self.parse_expression(pstate, _PREC_PLUS)
            did_something = True
        elif next_tag is _times and _PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp *= self.parse_expression(pstate, _PREC_TIMES)
            did_something = True
        elif next_tag is _floordiv and _PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp //= self.parse_expression(pstate, _PREC_TIMES)
            did_something = True
        elif next_tag is _over and _PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp /= self.parse_expression(pstate, _PREC_TIMES)
            did_something = True
        elif next_tag is _modulo and _PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp %= self.parse_expression(pstate, _PREC_TIMES)
            did_something = True
        elif next_tag is _power and _PREC_POWER > min_precedence:
            pstate.advance()
            left_exp **= self.parse_expression(pstate, _PREC_POWER)
            did_something = True
        elif next_tag is _and and _PREC_LOGICAL_AND > min_precedence:
            pstate.advance()
            from pymbolic.primitives import LogicalAnd
            left_exp = LogicalAnd((
                    left_exp,
                    self.parse_expression(pstate, _PREC_LOGICAL_AND)))
            did_something = True
        elif next_tag is _or and _PREC_LOGICAL_OR > min_precedence:
            pstate.advance()
            from pymbolic.primitives import LogicalOr
            left_exp = LogicalOr((
                    left_exp,
                    self.parse_expression(pstate, _PREC_LOGICAL_OR)))
            did_something = True
        elif next_tag is _bitwiseor and _PREC_BITWISE_OR > min_precedence:
            pstate.advance()
            from pymbolic.primitives import BitwiseOr
            left_exp = BitwiseOr((
                    left_exp,
                    self.parse_expression(pstate, _PREC_BITWISE_OR)))
            did_something = True
        elif next_tag is _bitwisexor and _PREC_BITWISE_XOR > min_precedence:
            pstate.advance()
            from pymbolic.primitives import BitwiseXor
            left_exp = BitwiseXor((
                    left_exp,
                    self.parse_expression(pstate, _PREC_BITWISE_XOR)))
            did_something = True
        elif next_tag is _bitwiseand and _PREC_BITWISE_AND > min_precedence:
            pstate.advance()
            from pymbolic.primitives import BitwiseAnd
            left_exp = BitwiseAnd((
                    left_exp,
                    self.parse_expression(pstate, _PREC_BITWISE_AND)))
            did_something = True
        elif next_tag is _rightshift and _PREC_SHIFT > min_precedence:
            pstate.advance()
            from pymbolic.primitives import RightShift
            left_exp = RightShift(
                    left_exp,
                    self.parse_expression(pstate, _PREC_SHIFT))
            did_something = True
        elif next_tag is _leftshift and _PREC_SHIFT > min_precedence:
            pstate.advance()
            from pymbolic.primitives import LeftShift
            left_exp = LeftShift(
                    left_exp,
                    self.parse_expression(pstate, _PREC_SHIFT))
            did_something = True
        elif next_tag in self._COMP_TABLE and _PREC_COMPARISON > min_precedence:
            pstate.advance()
            from pymbolic.primitives import Comparison
            left_exp = Comparison(
                    left_exp,
                    self._COMP_TABLE[next_tag],
                    self.parse_expression(pstate, _PREC_COMPARISON))
            did_something = True
        elif next_tag is _colon and _PREC_SLICE >= min_precedence:
            pstate.advance()
            expr_pstate = pstate.copy()

            assert not isinstance(left_exp, primitives.Slice)

            from pytools.lex import ParseError
            try:
                next_expr = self.parse_expression(expr_pstate, _PREC_SLICE)
            except ParseError:
                # no expression follows, too bad.
                left_exp = primitives.Slice((left_exp, None,))
            else:
                left_exp = _join_to_slice(left_exp, next_expr)
                pstate.assign(expr_pstate)

        elif next_tag is _comma and _PREC_COMMA > min_precedence:
            # The precedence makes the comma left-associative.

            pstate.advance()
            if pstate.is_at_end() or pstate.next_tag() is _closepar:
                left_exp = (left_exp,)
            else:
                new_el = self.parse_expression(pstate, _PREC_COMMA)
                if isinstance(left_exp, tuple) \
                        and not isinstance(left_exp, FinalizedTuple):
                    left_exp = left_exp + (new_el,)
                else:
                    left_exp = (left_exp, new_el)

            did_something = True

        return left_exp, did_something

    def parse_arglist(self, pstate):
        pstate.expect_not_end()

        args = []
        kwargs = {}

        comma_allowed = False
        while True:
            pstate.expect_not_end()

            saw_comma = False
            if pstate.next_tag() is _comma:
                saw_comma = True
                if not comma_allowed:
                    pstate.raise_parse_error("comma not expected")
                pstate.advance()
                pstate.expect_not_end()

            if pstate.next_tag() is _closepar:
                pstate.advance()
                return tuple(args), kwargs

            if not saw_comma and comma_allowed:
                pstate.raise_parse_error("comma expected")

            if (pstate.next_tag() is _identifier
                    and not pstate.is_at_end(1)
                    and pstate.next_tag(1) == _assign):
                kw = pstate.next_str()
                pstate.advance()
                pstate.advance()

                kwargs[kw] = self.parse_expression(pstate, _PREC_COMMA)
            else:
                if kwargs:
                    pstate.raise_parse_error(
                            "positional argument after keyword "
                            "argument not allowed")

                args.append(self.parse_expression(pstate, _PREC_COMMA))

            comma_allowed = True

    def __call__(self, expr_str, min_precedence=0):
        lex_result = [(tag, s, idx, match_obj)
                for (tag, s, idx, match_obj) in pytools.lex.lex(
                    self.lex_table, expr_str,
                    match_objects=True)
                if tag is not _whitespace]
        pstate = pytools.lex.LexIterator(lex_result, expr_str)

        result = self. parse_expression(pstate, min_precedence)
        if not pstate.is_at_end():
            pstate.raise_parse_error("leftover input after completed parse")
        return result

parse = Parser()
