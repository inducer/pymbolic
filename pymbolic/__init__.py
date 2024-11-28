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


from functools import partial

from pytools import module_getattr_for_deprecations

from . import compiler, parser, primitives
from .compiler import compile
from .mapper import (
    dependency,
    differentiator,
    distributor,
    evaluator,
    flattener,
    stringifier,
    substitutor,
)
from .mapper.differentiator import differentiate, differentiate as diff
from .mapper.distributor import distribute, distribute as expand
from .mapper.evaluator import evaluate, evaluate_kw
from .mapper.flattener import flatten
from .mapper.substitutor import substitute
from .parser import parse
from .primitives import (  # noqa: N813
    ExpressionNode,
    Variable,
    Variable as var,
    disable_subscript_by_getitem,
    expr_dataclass,
    flattened_product,
    flattened_sum,
    linear_combination,
    make_common_subexpression as cse,
    make_sym_vector,
    quotient,
    subscript,
    variables,
)
from .typing import (
    ArithmeticExpression,
    Bool,
    Expression,
    Expression as _TypingExpression,
    Number,
    RealNumber,
    Scalar,
)
from pymbolic.version import VERSION_TEXT as __version__  # noqa


__all__ = (
    "ArithmeticExpression",
    "Bool",
    "Expression",
    "ExpressionNode",
    "Number",
    "RealNumber",
    "Scalar",
    "Variable",
    "compile",
    "compiler",
    "cse",
    "dependency",
    "diff",
    "differentiate",
    "differentiator",
    "disable_subscript_by_getitem",
    "distribute",
    "distributor",
    "evaluate",
    "evaluate_kw",
    "evaluator",
    "expand",
    "expr_dataclass",
    "flatten",
    "flattened_product",
    "flattened_sum",
    "flattener",
    "linear_combination",
    "make_sym_vector",
    "parse",
    "parser",
    "primitives",
    "quotient",
    "stringifier",
    "subscript",
    "substitute",
    "substitutor",
    "var",
    "variables",
)

__getattr__ = partial(module_getattr_for_deprecations, __name__, {
        "ExpressionT": ("pymbolic.typing.Expression", _TypingExpression, 2026),
        "ArithmeticExpressionT": ("ArithmeticExpression", ArithmeticExpression, 2026),
        "BoolT": ("Bool", Bool, 2026),
        "ScalarT": ("Scalar", Scalar, 2026),
        })
