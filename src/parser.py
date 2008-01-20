import pymbolic.primitives as primitives
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

_LEX_TABLE = [
    (_imaginary, (_float, pytools.lex.RE("j"))),
    (_float, ("|", 
               pytools.lex.RE(r"[0-9]+\.[0-9]*([eE]-?[0-9]+)?"),
               pytools.lex.RE(r"[0-9]+(\.[0-9]*)?[eE]-?[0-9]+"),
               pytools.lex.RE(r"[0-9]*\.[0-9]+([eE]-?[0-9]+)?"),
               pytools.lex.RE(r"[0-9]*(\.[0-9]+)?[eE]-?[0-9]+"))),
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
    (_identifier, pytools.lex.RE(r"[a-z_A-Z_][a-zA-Z_0-9]*")),
    (_whitespace, pytools.lex.RE("[ \n\t]*")),
    (_comma, pytools.lex.RE(",")),
    (_dot, pytools.lex.RE(".")),
    ]

_PREC_PLUS = 10
_PREC_TIMES = 20
_PREC_POWER = 30
_PREC_UNARY_MINUS = 40
_PREC_CALL = 50

def parse(expr_str):
    def parse_terminal(pstate):
        next_tag = pstate.next_tag()
        if next_tag is _int:
            return int(pstate.next_str_and_advance())
        elif next_tag is _float:
            return float(pstate.next_str_and_advance())
        elif next_tag is _imaginary:
            return complex(pstate.next_str_and_advance())
        elif next_tag is _identifier:
            return primitives.Variable(pstate.next_str_and_advance())
        else:
            pstate.expected("terminal")

    def parse_expr_list(pstate):
        result = [parse_expression(pstate)]
        while pstate.next_tag() is _comma:
            pstate.advance()
            result.append(parse_expression(pstate))
        return result

    def parse_expression(pstate, min_precedence=0):
        pstate.expect_not_end()

        if pstate.is_next(_minus):
            pstate.advance()
            return -parse_expression(pstate, _PREC_UNARY_MINUS)
        if pstate.is_next(_openpar):
            pstate.advance()
            left_exp = parse_expression(pstate)
            pstate.expect(_closepar)
            pstate.advance()
        else:
            left_exp = parse_terminal(pstate)

        did_something = True
        while did_something:
            did_something = False
            if pstate.is_at_end():
                return left_exp
            
            next_tag = pstate.next_tag()

            if next_tag is _openpar and _PREC_CALL > min_precedence:
                pstate.advance()
                pstate.expect_not_end()
                if pstate.next_tag is _closepar:
                    pstate.advance()
                    left_exp = primitives.Call(left_exp, ())
                else:
                    left_exp = primitives.Call(left_exp, 
                                             tuple(parse_expr_list(pstate)))
                    pstate.expect(_closepar)
                    pstate.advance()
                did_something = True
            elif next_tag is _openbracket and _PREC_CALL > min_precedence:
                pstate.advance()
                pstate.expect_not_end()
                left_exp = primitives.Subscript(left_exp, parse_expression(pstate))
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
                left_exp += parse_expression(pstate, _PREC_PLUS)
                did_something = True
            elif next_tag is _minus and _PREC_PLUS > min_precedence:
                pstate.advance()
                left_exp -= parse_expression(pstate, _PREC_PLUS)
                did_something = True
            elif next_tag is _times and _PREC_TIMES > min_precedence:
                pstate.advance()
                left_exp *= parse_expression(pstate, _PREC_TIMES)
                did_something = True
            elif next_tag is _over and _PREC_TIMES > min_precedence:
                pstate.advance()
                left_exp /= parse_expression(pstate, _PREC_TIMES)
                did_something = True
            elif next_tag is _power and _PREC_POWER > min_precedence:
                pstate.advance()
                left_exp **= parse_expression(pstate, _PREC_POWER)
                did_something = True

        return left_exp

        
    pstate = pytools.lex.LexIterator(
        [(tag, s, idx) 
         for (tag, s, idx) in pytools.lex.lex(_LEX_TABLE, expr_str)
         if tag is not _whitespace], expr_str)

    result = parse_expression(pstate)
    if not pstate.is_at_end():
        print pstate.next_tag()
        pstate.raise_parse_error("leftover input after completed parse")
    return result


