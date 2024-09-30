# See https://github.com/inducer/pymbolic/pull/110 for context

import sys

from pymbolic import parse
from pymbolic.mapper import CachedIdentityMapper
from pymbolic.mapper.optimize import optimize_mapper
from pymbolic.primitives import Variable


code = ("(-1)*((cse_577[_pt_data_48[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        "_pt_data_49[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_48[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_577[_pt_data_46[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_47[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_46[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_577[_pt_data_7[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_43[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_7[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_577[_pt_data_44[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_45[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_44[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_579[_pt_data_68[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_69[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_68[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_579[_pt_data_66[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_67[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_66[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_579[_pt_data_50[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_63[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_50[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_579[_pt_data_64[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_65[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_64[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_581[_pt_data_88[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_89[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_88[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_581[_pt_data_86[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_87[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_86[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_581[_pt_data_70[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_83[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_70[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_581[_pt_data_84[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_85[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_84[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_582[_pt_data_107[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_108[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_107[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_582[_pt_data_105[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0],"
        " _pt_data_106[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_105[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_582[_pt_data_90[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_102[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_90[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_582[_pt_data_103[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_104[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_103[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0))"
        " + (cse_572[_pt_data_48[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_49[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_48[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0) "
        "+ (cse_572[_pt_data_46[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_47[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_46[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0) "
        "+ (cse_572[_pt_data_7[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_43[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_7[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_572[_pt_data_44[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_45[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_44[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_573[_pt_data_68[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_69[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_68[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_573[_pt_data_66[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_67[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_66[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_573[_pt_data_50[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_63[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_50[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_573[_pt_data_64[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_65[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_64[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_574[_pt_data_88[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_89[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_88[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_574[_pt_data_86[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_87[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_86[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0) "
        "+ (cse_574[_pt_data_70[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_83[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_70[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_574[_pt_data_84[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_85[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_84[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_575[_pt_data_107[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_108[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_107[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_575[_pt_data_105[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_106[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_105[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_575[_pt_data_90[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_102[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_90[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        " + (cse_575[_pt_data_103[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0], _pt_data_104[(iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 10]]"
        " if _pt_data_103[((iface_ensm15*1075540 + iel_ensm15*10 + idof_ensm15) % 4302160) // 10, 0] != -1 else 0)"
        )

expr = parse(code)
expr = CachedIdentityMapper()(expr)  # remove duplicate nodes


replacements = {
        "iface_ensm15": Variable("_0"),
        "iel_ensm15": Variable("_1"),
        "idof_ensm15": Variable("_2"),
        }


@optimize_mapper(drop_args=True, drop_kwargs=True,
                 # inline_cache=True, inline_rec=True,
                 inline_get_cache_key=True,
                 print_modified_code_file=sys.stdout)
class Renamer(CachedIdentityMapper):
    def map_variable(self, expr):
        return replacements.get(expr.name, expr)

    def get_cache_key(self, expr):
        # Must add 'type(expr)', to differentiate between python scalar types.
        # In Python, the following conditions are true: "hash(4) == hash(4.0)"
        # and "4 == 4.0", but their traversal results cannot be re-used.
        return (type(expr), expr)


def main():
    mapper = Renamer()
    mapper(expr)
    # print(type(new_expr))


if __name__ == "__main__":
    from time import time

    if 1:
        t_start = time()
        for _ in range(10_000):
            main()
        t_end = time()
        print(f"Took: {t_end-t_start} secs.")
    else:
        import pyinstrument
        from pyinstrument.renderers import SpeedscopeRenderer
        prof = pyinstrument.Profiler()
        with prof:
            for _ in range(10_000):
                main()
        with open("ss.json", "w") as outf:
            outf.write(prof.output(SpeedscopeRenderer(show_all=True)))
