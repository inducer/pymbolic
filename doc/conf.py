from importlib import metadata
from urllib.request import urlopen


_conf_url = "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())

copyright = "2013-24, Andreas Kloeckner"
release = metadata.version("pymbolic")
version = ".".join(release.split(".")[:2])

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

intersphinx_mapping = {
    "galgebra": ("https://galgebra.readthedocs.io/en/latest/", None),
    "mako": ("https://docs.makotemplates.org/en/latest/", None),
    "matchpy": ("https://matchpy.readthedocs.io/en/latest/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3", None),
    "sympy": ("https://docs.sympy.org/dev/", None),
    "pytools": ("https://documen.tician.de/pytools/", None),
    "typing_extensions":
        ("https://typing-extensions.readthedocs.io/en/latest/", None),
    "constantdict":
        ("https://matthiasdiener.github.io/constantdict/", None)
}

autodoc_type_aliases = {
    "Expression": "Expression",
    "ArithmeticExpression": "ArithmeticExpression",
}

nitpick_ignore_regex = [
    # Sphinx started complaining about these in 8.2.1(-ish)
    # -AK, 2025-02-24
    ["py:class", r"TypeAliasForwardRef"],
]

sphinxconfig_missing_reference_aliases = {
    # numpy
    "NDArray": "obj:numpy.typing.NDArray",
    "DTypeLike": "obj:numpy.typing.DTypeLike",
    "np.inexact": "class:numpy.inexact",
    "np.generic": "class:numpy.generic",
    # pytools typing
    "T": "class:pytools.T",
    "ShapeT": "class:pytools.obj_array.ShapeT",
    "ObjectArray": "class:pytools.obj_array.ObjectArray",
    "ObjectArray1D": "class:pytools.obj_array.ObjectArray",
    # pymbolic typing
    "ArithmeticExpression": "data:pymbolic.typing.ArithmeticExpression",
    "Expression": "data:pymbolic.typing.Expression",
    "p.AlgebraicLeaf": "class:pymbolic.primitives.AlgebraicLeaf",
    "ExpressionNode": "class:pymbolic.primitives.ExpressionNode",
    "_Expression": "class:pymbolic.primitives.ExpressionNode",
    "Lookup": "class:pymbolic.primitives.Lookup",
    "LogicalAnd": "class:pymbolic.primitives.LogicalAnd",
    "LogicalOr": "class:pymbolic.primitives.LogicalOr",
    "LogicalNot": "class:pymbolic.primitives.LogicalNot",
    "Comparison": "class:pymbolic.primitives.Comparison",
}


def setup(app):
    app.connect("missing-reference", process_autodoc_missing_reference)  # noqa: F821


import sys


sys._BUILDING_SPHINX_DOCS = True
