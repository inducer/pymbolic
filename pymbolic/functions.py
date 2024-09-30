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


import pymbolic.primitives as p


def sin(x):
    return p.Call(p.Lookup(p.Variable("math"), "sin"), (x,))


def cos(x):
    return p.Call(p.Lookup(p.Variable("math"), "cos"), (x,))


def tan(x):
    return p.Call(p.Lookup(p.Variable("math"), "tan"), (x,))


def log(x):
    return p.Call(p.Lookup(p.Variable("math"), "log"), (x,))


def exp(x):
    return p.Call(p.Lookup(p.Variable("math"), "exp"), (x,))


def sinh(x):
    return p.Call(p.Lookup(p.Variable("math"), "sinh"), (x,))


def cosh(x):
    return p.Call(p.Lookup(p.Variable("math"), "cosh"), (x,))


def tanh(x):
    return p.Call(p.Lookup(p.Variable("math"), "tanh"), (x,))


def expm1(x):
    return p.Call(p.Lookup(p.Variable("math"), "expm1"), (x,))


def fabs(x):
    return p.Call(p.Lookup(p.Variable("math"), "fabs"), (x,))


def sign(x):
    return p.Call(p.Lookup(p.Variable("math"), "copysign"), (1, x,))
