import primitives
import lex

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

_LEX_TABLE = [
    (_imaginary, (_float, lex.RE("j"))),
    (_float, ("|", 
               lex.RE(r"-?[0-9]*\.[0-9]+([eE][0-9]+)?"),
               lex.RE(r"-?[0-9]*(\.[0-9]+)?[eE][0-9]+"))),
    (_int, lex.RE(r"-?[0-9]+")),
    (_plus, lex.RE(r"\+")),
    (_minus, lex.RE(r"-")),
    (_power, lex.RE(r"\*\*")),
    (_times, lex.RE(r"\*")),
    (_over, lex.RE(r"/")),
    (_openpar, lex.RE(r"\(")),
    (_closepar, lex.RE(r"\)")),
    (_openbracket, lex.RE(r"\[")),
    (_closebracket, lex.RE(r"\]")),
    (_identifier, lex.RE(r"[a-zA-Z_]+")),
    (_whitespace, lex.RE("[ \n\t]*")),
    (_comma, lex.RE(",")),
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
            return primitives.Constant(int(pstate.next_str_and_advance()))
        elif next_tag is _float:
            return primitives.Constant(float(pstate.next_str_and_advance()))
        elif next_tag is _imaginary:
            return primitives.Constant(complex(pstate.next_str_and_advance()))
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
            return primitives.Negation(parse_expression(pstate, _PREC_UNARY_MINUS))
        if pstate.is_next(_openpar):
            pstate.advance()
            result = parse_expression(pstate)
            pstate.expect(_closepar)
            return result

        left_exp = parse_terminal(pstate)

        if pstate.is_at_end():
            return left_exp

        next_tag = pstate.next_tag()

        if next_tag is _openpar and _PREC_CALL >= min_precedence:
            pstate.advance()
            pstate.expect_not_end()
            if pstate.next_tag is _closepar:
                pstate.advance()
                return primitives.Call(left_exp, ())
            else:
                result = primitives.Call(left_exp, 
                                         tuple(parse_expr_list(pstate)))
                pstate.expect(_closepar)
                return result

        if next_tag is _plus and _PREC_PLUS >= min_precedence:
            pstate.advance()
            return left_exp+parse_expression(pstate, _PREC_PLUS)
        elif next_tag is _minus and _PREC_PLUS >= min_precedence:
            pstate.advance()
            return left_exp-primitives.Negation(parse_expression(pstate, _PREC_PLUS))
        elif next_tag is _times and _PREC_TIMES >= min_precedence:
            pstate.advance()
            return left_exp*parse_expression(pstate, _PREC_TIMES)
        elif next_tag is _over and _PREC_TIMES >= min_precedence:
            pstate.advance()
            return left_exp/parse_expression(pstate, _PREC_TIMES)
        elif next_tag is _power and _PREC_POWER >= min_precedence:
            pstate.advance()
            return left_exp**parse_expression(pstate, _PREC_TIMES)
        else:
            return left_exp

        
    pstate = lex.LexIterator([(tag, s, idx) 
                              for (tag, s, idx) in lex.lex(_LEX_TABLE, expr_str)
                              if tag is not _whitespace], expr_str)

    return parse_expression(pstate)
    
