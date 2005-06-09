import re

class RuleError:
    def __init__(self, rule):
        self.Rule = s

    def __str__(self):
        return repr(self.Rule)

class InvalidTokenError:
    def __init__(self, s, str_index):
        self.String = s
        self.Index = str_index

    def __str__(self):
        return "at index %d: ...%s..." % \
               (self.Index, self.String[self.Index:self.Index+20])

class ParseError:
    def __init__(self, msg, s, token):
        self.Message = msg
        self.String = s
        self.Token = token

    def __str__(self):
        if self.Token is None:
            return "%s at end of input" % self.Message
        else:
            return "%s at index %d: ...%s..." % \
                   (self.Message, self.Token[2], self.String[self.Token[2]:self.Token[2]+20])




class RE:
    def __init__(self, str):
        self.Content = str
        self.RE = re.compile(str)

    def __repr__(self):
        return "RE(%s)" % self.Content




def lex(lex_table, str, debug=False):
    rule_dict = dict(lex_table)

    def matches_rule(rule, str, start):
        if debug:
            print "Trying", rule, "on", str[start:]
        if isinstance(rule, tuple):
            if rule[0] == "|":
                for subrule in rule[1:]:
                    length = matches_rule(subrule, str, start)
                    if length:
                        return length
            else:
                my_match_length = 0
                for subrule in rule:
                    length = matches_rule(subrule, str, start)
                    if length:
                        my_match_length += length
                        start += length
                    else:
                        return 0
                return my_match_length
        elif isinstance(rule, basestring):
            return matches_rule(rule_dict[rule], str, start)
        elif isinstance(rule, RE):
            match_obj = rule.RE.match(str, start)
            if match_obj:
                return match_obj.end()-start
            else:
                return 0
        else:
            raise RuleError, rule

    result = []
    i = 0
    while i < len(str):
        rule_matched = False
        for name, rule in lex_table:
            length = matches_rule(rule, str, i)
            if length:
                result.append((name, str[i:i+length], i))
                i += length
                rule_matched = True
                break
        if not rule_matched:
            raise InvalidTokenError, (str, i)
    return result




class LexIterator:
    def __init__(self, lexed, raw_str, lex_index=0):
        self.Lexed = lexed
        self.RawString = raw_str
        self.Index = lex_index
        
    def next_tag(self):
        return self.Lexed[self.Index][0]

    def next_str(self):
        return self.Lexed[self.Index][1]

    def next_str_and_advance(self):
        result = self.next_str()
        self.advance()
        return result
    
    def advance(self):
        self.Index += 1

    def is_at_end(self):
        return self.Index >= len(self.Lexed)

    def is_next(self, tag):
        return self.next_tag() is tag

    def raise_parse_error(self, msg):
        if self.is_at_end():
            raise ParseError, (msg, self.RawString, None)
        else:
            raise ParseError, (msg, self.RawString, self.Lexed[self.Index])

    def expected(self, what_expected):
        if self.is_at_end():
            self.raise_parse_error("%s expected, end of input found instead" % \
                                   what_expected)
        else:
            self.raise_parse_error("%s expected, %s found instead" % \
                                   (what_expected, str(self.next_tag())))

    def expect(self, tag):
        if not self.is_next(tag):
            self.expected(str(tag))
        self.advance()

    def expect_not_end(self):
        if self.is_at_end():
            self.raise_parse_error("unexpected end of input")


