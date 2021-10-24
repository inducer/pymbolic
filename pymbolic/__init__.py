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

import pymbolic.parser
import pymbolic.compiler

import pymbolic.mapper.evaluator
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency
import pymbolic.mapper.substitutor
import pymbolic.mapper.differentiator
import pymbolic.mapper.distributor
import pymbolic.mapper.flattener
import pymbolic.primitives

from pymbolic.polynomial import Polynomial  # noqa

var = pymbolic.primitives.Variable
variables = pymbolic.primitives.variables
flattened_sum = pymbolic.primitives.flattened_sum
subscript = pymbolic.primitives.subscript
flattened_product = pymbolic.primitives.flattened_product
quotient = pymbolic.primitives.quotient
linear_combination = pymbolic.primitives.linear_combination
cse = pymbolic.primitives.make_common_subexpression
make_sym_vector = pymbolic.primitives.make_sym_vector

disable_subscript_by_getitem = pymbolic.primitives.disable_subscript_by_getitem

parse = pymbolic.parser.parse
evaluate = pymbolic.mapper.evaluator.evaluate
evaluate_kw = pymbolic.mapper.evaluator.evaluate_kw
compile = pymbolic.compiler.compile
substitute = pymbolic.mapper.substitutor.substitute
diff = differentiate = pymbolic.mapper.differentiator.differentiate
expand = pymbolic.mapper.distributor.distribute
distribute = pymbolic.mapper.distributor.distribute
flatten = pymbolic.mapper.flattener.flatten
