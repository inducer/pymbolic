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


from pymbolic.version import VERSION_TEXT as __version__  # noqa

from . import parser
from . import compiler

from .mapper import evaluator
from .mapper import stringifier
from .mapper import dependency
from .mapper import substitutor
from .mapper import differentiator
from .mapper import distributor
from .mapper import flattener
from . import primitives

from .primitives import (Variable as var,  # noqa: N813
    Variable,
    Expression,
    variables,
    flattened_sum,
    subscript,
    flattened_product,
    quotient,
    linear_combination,
    make_common_subexpression as cse,
    make_sym_vector,
    disable_subscript_by_getitem,
    expr_dataclass,
)
from .parser import parse
from .mapper.evaluator import evaluate
from .mapper.evaluator import evaluate_kw
from .compiler import compile
from .mapper.substitutor import substitute
from .mapper.differentiator import differentiate as diff
from .mapper.differentiator import differentiate
from .mapper.distributor import distribute as expand
from .mapper.distributor import distribute
from .mapper.flattener import flatten
from .typing import NumberT, ScalarT, ArithmeticExpressionT, ExpressionT, BoolT


__all__ = (
    "ArithmeticExpressionT",
    "BoolT",
    "Expression",
    "ExpressionT",
    "NumberT",
    "ScalarT",
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
