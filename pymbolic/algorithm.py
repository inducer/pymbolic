"""
.. autofunction:: integer_power
.. autofunction:: extended_euclidean
.. autofunction:: gcd
.. autofunction:: lcm
.. autofunction:: fft
.. autofunction:: ifft
.. autofunction:: sym_fft
.. autofunction:: reduced_row_echelon_form
.. autofunction:: solve_affine_equations_for
"""

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

import operator
import sys
from typing import TYPE_CHECKING, overload
from warnings import warn

from pytools import MovedFunctionDeprecationWrapper, memoize


if TYPE_CHECKING or getattr(sys, "_BUILDING_SPHINX_DOCS", None):
    import numpy as np


# {{{ integer powers

def integer_power(x, n, one=1):
    """Compute :math:`x^n` using only multiplications.

    See also the `C2 wiki <https://wiki.c2.com/?IntegerPowerAlgorithm>`__.
    """

    assert isinstance(n, int)

    if n < 0:
        raise RuntimeError("the integer power algorithm does not "
                "work for negative numbers")

    aux = one

    while n > 0:
        if n & 1:
            aux *= x
            if n == 1:
                return aux
        x = x * x
        n //= 2

    return aux

# }}}


# {{{ euclidean algorithm

def extended_euclidean(q, r):
    """Return a tuple *(p, a, b)* such that :math:`p = aq + br`,
    where *p* is the greatest common divisor of *q* and *r*.

    See also the
    `Wikipedia article on the Euclidean algorithm
    <https://en.wikipedia.org/wiki/Euclidean_algorithm>`__.
    """
    import pymbolic.traits as traits

    # see [Davenport], Appendix, p. 214

    t = traits.common_traits(q, r)

    if t.norm(q) < t.norm(r):
        p, a, b = extended_euclidean(r, q)
        return p, b, a

    Q = 1, 0  # noqa
    R = 0, 1  # noqa

    while r:
        quot, t = divmod(q, r)
        T = Q[0] - quot*R[0], Q[1] - quot*R[1]  # noqa
        q, r = r, t
        Q, R = R, T  # noqa: N806

    return q, Q[0], Q[1]


def gcd(q, r):
    return extended_euclidean(q, r)[0]


def gcd_many(*args):
    if len(args) == 0:
        return 1
    elif len(args) == 1:
        return args[0]
    else:
        from functools import reduce
        return reduce(gcd, args)


def lcm(q, r):
    return abs(q*r)//gcd(q, r)

# }}}


# {{{ fft

@memoize
def find_factors(n):
    from math import sqrt

    n1 = 2
    max_n1 = int(sqrt(n))+1
    while n % n1 != 0 and n1 <= max_n1:
        n1 += 1

    if n1 > max_n1:
        n1 = n

    n2 = n // n1

    return n1, n2


def fft(x, sign=1,
        wrap_intermediate=None,
        *,
        wrap_intermediate_with_level=None,
        complex_dtype=None,
        custom_np=None, level=0):
    r"""Computes the Fourier transform of x:

    .. math::

        F[x]_k = \sum_{j=0}^{n-1} z^{kj} x_j

    where :math:`z = \exp(-2i\pi\operatorname{sign}/n)` and ``n == len(x)``.
    Works for all positive *n*.

    See also `Wikipedia <https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm>`__.
    """

    # revision 293076305
    # https://en.wikipedia.org/w/index.php?title=Cooley-Tukey_FFT_algorithm&oldid=293076305

    # {{{ parameter processing

    if wrap_intermediate is not None and wrap_intermediate_with_level is not None:
        raise TypeError("may specify at most one of wrap_intermediate and "
                "wrap_intermediate_with_level")
    if wrap_intermediate is not None:
        from warnings import warn
        warn("wrap_intermediate is deprecated. Use wrap_intermediate_with_level "
                "instead. wrap_intermediate will stop working in 2023.",
                DeprecationWarning, stacklevel=2)

        def wrap_intermediate_with_level(level, x):  # pylint: disable=function-redefined
            return wrap_intermediate(x)

    if wrap_intermediate_with_level is None:
        def wrap_intermediate_with_level(level, x):
            return x

    from math import pi
    if custom_np is None:
        import numpy as custom_np

    if complex_dtype is None:
        if x.dtype.kind == "c":
            complex_dtype = x.dtype
        else:
            from warnings import warn
            warn("Not supplying complex_dtype is deprecated, falling back "
                    "to complex128 for now. This will stop working in 2023.",
                    DeprecationWarning, stacklevel=2)

            complex_dtype = custom_np.complex128

    complex_dtype = custom_np.dtype(complex_dtype)

    # }}}

    n = len(x)

    if n == 1:
        return x

    N1, N2 = find_factors(n)  # noqa: N806

    scalar_tp = complex_dtype.type
    sub_ffts = [
            wrap_intermediate_with_level(level,
                fft(x[n1::N1], sign, wrap_intermediate, custom_np=custom_np,
                    level=level+1, complex_dtype=complex_dtype)
                * custom_np.exp(
                    sign*-2j*pi*n1/(N1*N2)
                    * custom_np.arange(0, N2, dtype=complex_dtype)))
            for n1 in range(N1)]

    return custom_np.concatenate([
        sum(subvec * scalar_tp(custom_np.exp(sign*(-2j)*pi*n1*k1/N1))
            for n1, subvec in enumerate(sub_ffts))
        for k1 in range(N1)
        ], axis=0)


def ifft(x, wrap_intermediate=None,
         *,
         wrap_intermediate_with_level=None,
         complex_dtype=None,
         custom_np=None):
    return (1/len(x))*fft(x, sign=-1, wrap_intermediate=wrap_intermediate,
            wrap_intermediate_with_level=wrap_intermediate_with_level,
            complex_dtype=complex_dtype, custom_np=custom_np)


def sym_fft(x, sign=1):
    """Perform a (symbolic) FFT on the :mod:`numpy` object array x.

    Remove near-zero floating point constants, insert
    :class:`pymbolic.primitives.CommonSubexpression`
    wrappers at opportune points.
    """

    from pymbolic.mapper import CSECachingMapperMixin, IdentityMapper

    class NearZeroKiller(CSECachingMapperMixin, IdentityMapper):
        map_common_subexpression_uncached = \
                IdentityMapper.map_common_subexpression

        def map_constant(self, expr):
            if isinstance(expr, complex):
                r = expr.real
                i = expr.imag
                if abs(r) < 1e-15:
                    r = 0
                if abs(i) < 1e-15:
                    i = 0
                if i == 0:
                    return r
                else:
                    return complex(r, i)
            else:
                return expr

    import numpy

    def wrap_intermediate(x):
        if len(x) > 1:
            from pymbolic.primitives import CommonSubexpression, cse_scope

            result = numpy.empty(len(x), dtype=object)
            for i, x_i in enumerate(x):
                result[i] = CommonSubexpression(x_i, scope=cse_scope.EVALUATION)

            return result
        else:
            return x

    return NearZeroKiller()(
            fft(wrap_intermediate(x), sign=sign,
                wrap_intermediate=wrap_intermediate))

# }}}


def csr_matrix_multiply(S, x):  # noqa
    """Multiplies a :class:`scipy.sparse.csr_matrix` S by an object-array vector x.
    """
    h, _w = S.shape

    import numpy
    result = numpy.empty_like(x)

    for i in range(h):
        result[i] = sum(S.data[idx]*x[S.indices[idx]]  # pylint:disable=unsupported-assignment-operation
                for idx in range(S.indptr[i], S.indptr[i+1]))

    return result


# {{{ reduced_row_echelon_form

@overload
def reduced_row_echelon_form(
            mat: np.ndarray,
            *, integral: bool | None = None,
        ) -> np.ndarray:
    ...


@overload
def reduced_row_echelon_form(
            mat: np.ndarray,
            rhs: np.ndarray,
            *, integral: bool | None = None,
        ) -> tuple[np.ndarray, np.ndarray]:
    ...


def reduced_row_echelon_form(
            mat: np.ndarray,
            rhs: np.ndarray | None = None,
            integral: bool | None = None,
        ) -> tuple[np.ndarray, np.ndarray] | np.ndarray:
    m, n = mat.shape

    mat = mat.copy()
    if rhs is not None:
        rhs = rhs.copy()

    if integral is None:
        warn(
             "Not specifying 'integral' is deprecated, please add it as an argument. "
             "This will stop being supported in 2025.",
             DeprecationWarning, stacklevel=2)

    if integral:
        div_func = operator.floordiv
    else:
        div_func = operator.truediv

    i = 0
    j = 0

    while i < m and j < n:
        # {{{ find pivot in column j, starting in row i

        nonz_row = None
        for k in range(i, m):
            if mat[k, j]:
                nonz_row = k
                break

        # }}}

        if nonz_row is not None:
            # swap rows i and nonz
            mat[i], mat[nonz_row] = \
                    (mat[nonz_row].copy(), mat[i].copy())
            if rhs is not None:
                rhs[i], rhs[nonz_row] = \
                        (rhs[nonz_row].copy(), rhs[i].copy())

            for u in range(0, m):
                if u == i:
                    continue
                if not mat[u, j]:
                    # already 0
                    continue

                ell = lcm(mat[u, j], mat[i, j])
                u_fac = div_func(ell, mat[u, j])
                i_fac = div_func(ell, mat[i, j])

                mat[u] = u_fac*mat[u] - i_fac*mat[i]
                if rhs is not None:
                    rhs[u] = u_fac*rhs[u] - i_fac*rhs[i]

                assert mat[u, j] == 0

            i += 1

        j += 1

    if integral:
        for i in range(m):
            g = gcd_many(*(
                [a for a in mat[i] if a]
                +
                [a for a in rhs[i] if a] if rhs is not None else []))

            mat[i] //= g
            if rhs is not None:
                rhs[i] //= g

    import numpy as np

    from pymbolic.mapper.flattener import flatten
    vec_flatten = np.vectorize(flatten, otypes=[object])

    for i in range(m):
        mat[i] = vec_flatten(mat[i])
        if rhs is not None:
            rhs[i] = vec_flatten(rhs[i])

    if rhs is None:
        return mat
    else:
        return mat, rhs

# }}}


gaussian_elimination = MovedFunctionDeprecationWrapper(reduced_row_echelon_form, "2025")


# {{{ symbolic (linear) equation solving

def solve_affine_equations_for(unknowns, equations):
    """
    :arg unknowns: A list of variable names for which to solve.
    :arg equations: A list of tuples ``(lhs, rhs)``.
    :return: a dict mapping unknown names to their values.
    """
    import numpy as np

    from pymbolic.mapper.dependency import DependencyMapper
    dep_map = DependencyMapper(composite_leaves=True)

    # fix an order for unknowns
    from pymbolic import var
    unknowns = [var(u) for u in unknowns]
    unknowns_set = set(unknowns)
    unknown_idx_lut = {tgt_name: idx
            for idx, tgt_name in enumerate(unknowns)}

    # Find non-unknown variables, fix order for them
    # Last non-unknown is constant.
    parameters = set()
    for lhs, rhs in equations:
        parameters.update(dep_map(lhs) - unknowns_set)
        parameters.update(dep_map(rhs) - unknowns_set)

    parameters_list = list(parameters)
    parameter_idx_lut = {var_name: idx
            for idx, var_name in enumerate(parameters_list)}

    from pymbolic.mapper.coefficient import CoefficientCollector
    coeff_coll = CoefficientCollector()

    # {{{ build matrix and rhs

    mat = np.zeros((len(equations), len(unknowns_set)), dtype=object)
    rhs_mat = np.zeros((len(equations), len(parameters)+1), dtype=object)

    for i_eqn, (lhs, rhs) in enumerate(equations):
        for lhs_factor, coeffs in [(1, coeff_coll(lhs)), (-1, coeff_coll(rhs))]:
            for key, coeff in coeffs.items():
                if key in unknowns_set:
                    mat[i_eqn, unknown_idx_lut[key]] = lhs_factor*coeff
                elif key in parameters:
                    rhs_mat[i_eqn, parameter_idx_lut[key]] = -lhs_factor*coeff
                elif key == 1:
                    rhs_mat[i_eqn, -1] = -lhs_factor*coeff
                else:
                    raise ValueError(f"key '{key}' not understood")

    # }}}

    mat, rhs_mat = reduced_row_echelon_form(mat, rhs_mat, integral=True)

    # FIXME /!\ Does not check for overdetermined system.

    result = {}
    for j, unknown in enumerate(unknowns):
        (nonz_row,) = np.where(mat[:, j])
        if len(nonz_row) != 1:
            raise RuntimeError(f"cannot uniquely solve for '{unknown}'")

        (nonz_row,) = nonz_row

        if abs(mat[nonz_row, j]) != 1:
            raise RuntimeError(
                    f"division with remainder in linear solve for '{unknown}'")
        div = mat[nonz_row, j]

        unknown_val = int(rhs_mat[nonz_row, -1]) // div
        for parameter, coeff in zip(
                    parameters_list, rhs_mat[nonz_row, :-1], strict=True):
            unknown_val += (int(coeff) // div) * parameter

        result[unknown] = unknown_val

    if 0:
        for lhs, rhs in equations:
            print(lhs, "=", rhs)
        print("-------------------")
        for lhs, rhs in result.items():
            print(lhs, "=", rhs)

    return result

# }}}


# vim: foldmethod=marker
