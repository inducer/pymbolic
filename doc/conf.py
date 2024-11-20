from importlib import metadata
from urllib.request import urlopen


_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
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
    "typing_extensions":
        ("https://typing-extensions.readthedocs.io/en/latest/", None),
    "immutabledict":
        ("https://immutabledict.corenting.fr/", None)
}
autodoc_type_aliases = {
    "Expression": "Expression",
    "ArithmeticExpression": "ArithmeticExpression",
}


nitpick_ignore_regex = [
    # Avoids this error. Not sure where to even look.
    # <unknown>:1: WARNING: py:class reference target not found: ExpressionNode [ref.class]  # noqa: E501
    ["py:class", r"ExpressionNode"],
    ]


import sys


sys._BUILDING_SPHINX_DOCS = True
