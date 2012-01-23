import pytools.lex

_imaginary = intern("imaginary")
_float = intern("float")
_int = intern("int")
_power = intern("exp")
_plus = intern("plus")
_minus = intern("minus")
_times = intern("times")
_over = intern("over")
_openpar = intern("openpar")
_closepar = intern("closepar")
_openbracket = intern("openbracket")
_closebracket = intern("closebracket")
_identifier = intern("identifier")
_whitespace = intern("whitespace")
_comma = intern("comma")
_dot = intern("dot")

_PREC_COMMA = 5 # must be > 1 (1 is used by fortran-to-cl)
_PREC_LOGICAL_OR = 80
_PREC_LOGICAL_AND = 90
_PREC_COMPARISON = 100
_PREC_PLUS = 110
_PREC_TIMES = 120
_PREC_POWER = 130
_PREC_UNARY = 140
_PREC_CALL = 150




class Parser:
    lex_table = [
            (_imaginary, (_float, pytools.lex.RE("j"))),
            (_float, ("|",
                pytools.lex.RE(r"[+-]?[0-9]+\.[0-9]*([eEdD][+-]?[0-9]+)?"),
                pytools.lex.RE(r"[+-]?[0-9]+(\.[0-9]*)?[eEdD][+-]?[0-9]+"),
                pytools.lex.RE(r"[+-]?[0-9]*\.[0-9]+([eEdD][+-]?[0-9]+)?"),
                pytools.lex.RE(r"[+-]?[0-9]*(\.[0-9]+)?[eEdD][+-]?[0-9]+"))),
            (_int, pytools.lex.RE(r"[0-9]+")),
            (_plus, pytools.lex.RE(r"\+")),
            (_minus, pytools.lex.RE(r"-")),
            (_power, pytools.lex.RE(r"\*\*")),
            (_times, pytools.lex.RE(r"\*")),
            (_over, pytools.lex.RE(r"/")),
            (_openpar, pytools.lex.RE(r"\(")),
            (_closepar, pytools.lex.RE(r"\)")),
            (_openbracket, pytools.lex.RE(r"\[")),
            (_closebracket, pytools.lex.RE(r"\]")),
            (_identifier, pytools.lex.RE(r"[@a-z_A-Z_][@a-zA-Z_0-9]*")),
            (_whitespace, pytools.lex.RE("[ \n\t]*")),
            (_comma, pytools.lex.RE(",")),
            (_dot, pytools.lex.RE(r"\.")),
            ]

    def parse_terminal(self, pstate):
        import pymbolic.primitives as primitives

        next_tag = pstate.next_tag()
        if next_tag is _int:
            return int(pstate.next_str_and_advance())
        elif next_tag is _float:
            return float(pstate.next_str_and_advance()
                    .replace("d", "e").replace("D", "e"))
        elif next_tag is _imaginary:
            return complex(pstate.next_str_and_advance())
        elif next_tag is _identifier:
            return primitives.Variable(pstate.next_str_and_advance())
        else:
            pstate.expected("terminal")

    def parse_prefix(self, pstate):
        import pymbolic.primitives as primitives
        pstate.expect_not_end()

        if pstate.is_next(_times):
            pstate.advance()
            left_exp = primitives.Wildcard()
        elif pstate.is_next(_plus):
            pstate.advance()
            left_exp = self.parse_expression(pstate, _PREC_UNARY)
        elif pstate.is_next(_minus):
            pstate.advance()
            left_exp = -self.parse_expression(pstate, _PREC_UNARY)
        elif pstate.is_next(_openpar):
            pstate.advance()
            left_exp = self.parse_expression(pstate)
            pstate.expect(_closepar)
            pstate.advance()
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

            left_exp, did_something = self.parse_postfix(
                    pstate, min_precedence, left_exp)

        return left_exp

    def parse_postfix(self, pstate, min_precedence, left_exp):
        import pymbolic.primitives as primitives

        did_something = False

        next_tag = pstate.next_tag()

        if next_tag is _openpar and _PREC_CALL > min_precedence:
            pstate.advance()
            pstate.expect_not_end()
            if next_tag is _closepar:
                pstate.advance()
                left_exp = primitives.Call(left_exp, ())
            else:
                args = self.parse_expression(pstate)
                if not isinstance(args, tuple):
                    args = (args,)
                left_exp = primitives.Call(left_exp, args)
                pstate.expect(_closepar)
                pstate.advance()
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
        elif next_tag is _over and _PREC_TIMES > min_precedence:
            pstate.advance()
            left_exp /= self.parse_expression(pstate, _PREC_TIMES)
            did_something = True
        elif next_tag is _power and _PREC_POWER > min_precedence:
            pstate.advance()
            left_exp **= self.parse_expression(pstate, _PREC_POWER)
            did_something = True
        elif next_tag is _comma and _PREC_COMMA > min_precedence:
            # The precedence makes the comma left-associative.

            pstate.advance()
            if pstate.is_at_end() or pstate.next_tag() is _closepar:
                return (left_exp,)

            new_el = self.parse_expression(pstate, _PREC_COMMA)
            if isinstance(left_exp, tuple):
                left_exp = left_exp + (new_el,)
            else:
                left_exp = (left_exp, new_el)
            did_something = True

        return left_exp, did_something

    def __call__(self, expr_str):
        pstate = pytools.lex.LexIterator(
            [(tag, s, idx)
             for (tag, s, idx) in pytools.lex.lex(self.lex_table, expr_str)
             if tag is not _whitespace], expr_str)

        result = self. parse_expression(pstate)
        if not pstate.is_at_end():
            pstate.raise_parse_error("leftover input after completed parse")
        return result

parse = Parser()
