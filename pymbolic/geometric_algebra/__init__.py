from __future__ import division
from __future__ import absolute_import
import six
from six.moves import range

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

from pytools import memoize, memoize_method
import numpy as np


__doc__ = """
See `Wikipedia <https://en.wikipedia.org/wiki/Geometric_algebra>`_ for an idea
of what this is.

.. versionadded:: 2013.2

Also see :ref:`ga-examples`.

Spaces
------

.. autoclass:: Space

    .. autoattribute:: dimensions
    .. autoattribute:: is_orthogonal
    .. autoattribute:: is_euclidean

.. autofunction:: get_euclidean_space

Multivectors
------------

.. autoclass:: MultiVector

.. _ga-examples:

Example usage
-------------

This first example demonstrates how to compute a cross product using
:class:`MultiVector`:

.. doctest::

    >>> import numpy as np
    >>> import pymbolic.geometric_algebra as ga
    >>> MV = ga.MultiVector

    >>> a = np.array([3.344, 1.2, -0.5])
    >>> b = np.array([7.4, 1.1, -2.0])
    >>> np.cross(a, b)
    array([-1.85  ,  2.988 , -5.2016])

    >>> mv_a = MV(a)
    >>> mv_b = MV(b)
    >>> print -mv_a.I*(mv_a^mv_b)
    MV(-1.85*e0 + 2.988*e1 + -5.2016*e2)

This simple example demonstrates how a complex number is simply a special
case of a :class:`MultiVector`:

.. doctest::

    >>> import numpy as np
    >>> import pymbolic.geometric_algebra as ga
    >>> MV = ga.MultiVector
    >>>
    >>> sp = ga.Space(metric_matrix=-np.eye(1))
    >>> sp
    Space(['e0'], array([[-1.]]))

    >>> one = MV(1, sp)
    >>> one
    MultiVector({0: 1}, Space(['e0'], array([[-1.]])))
    >>> print one
    MV(1)
    >>> print one.I
    MV(1*e0)
    >>> print one.I ** 2
    MV(-1.0)

    >>> print (3+5j)*(2+3j)/(3j)
    (6.33333333333+3j)
    >>> print (3+5*one.I)*(2+3*one.I)/(3*one.I)
    MV(6.33333333333 + 3.0*e0)

The following test demonstrates the use of the object and shows many useful
properties:

.. literalinclude:: ../test/test_pymbolic.py
   :start-after: START_GA_TEST
   :end-before: END_GA_TEST

"""


# {{{ helpers

def permutation_sign(p):
    p = list(p)
    s = +1

    for i in range(len(p)):
        # j is the current position of item I.
        j = i

        while p[j] != i:
            j += 1

        # Unless the item is already in the correct place, restore it.
        if j != i:
            p[i], p[j] = p[j], p[i]
            s = -s

    return s


def bit_count(i):
    """Count the number of set bits in *i*."""

    # nicked from http://wiki.python.org/moin/BitManipulation

    count = 0
    while i:
        i &= i - 1
        count += 1
    return count


def canonical_reordering_sign(a_bits, b_bits):
    """Count the number of basis vector swaps required to
    get the combination of 'a_bits' and 'b_bits' into canonical order.

    :arg a_bits: bitmap representing basis blade *a*
    :arg b_bits: bitmap representing basis blade *b*

    Algorithm from figure 19.1 of [DFM] in :class:`MultiVector`.
    """

    a_bits = a_bits >> 1
    s = 0
    while a_bits:
        s = s + bit_count(a_bits & b_bits)
        a_bits = a_bits >> 1

    if s & 1:
        return -1
    else:
        return 1

# }}}


# {{{ space

class Space(object):
    """
    .. attribute :: basis_names

        A sequence of names of basis vectors.

    .. attribute :: metric_matrix

        A *(dims,dims)*-shaped matrix, whose *(i,j)*-th entry represents the
        inner product of basis vector *i* and basis vector *j*.
    """

    def __init__(self, basis=None, metric_matrix=None):
        """
        :arg basis: A sequence of names of basis vectors, or an integer (the
            number of dimensions) to use the default names ``e0`` through ``eN``.
        :arg metric_matrix: See :attr:`metric_matrix`.
            If *None*, the Euclidean metric is assumed.
        """

        if basis is None and metric_matrix is None:
            raise TypeError("at least one of 'basis' and 'metric_matrix' "
                    "must be passed")

        if basis is None:
            basis = int(metric_matrix.shape[0])

        if isinstance(basis, int):
            basis = ["e%d" % i for i in range(basis)]

        if metric_matrix is None:
            metric_matrix = np.eye(len(basis), dtype=np.object)

        from pytools import all
        if not (
                len(metric_matrix.shape) == 2
                and
                all(dim == len(basis) for dim in metric_matrix.shape)):
            raise ValueError("metric_matrix has the wrong shape")

        self.basis_names = basis
        self.metric_matrix = metric_matrix

    @property
    def dimensions(self):
        return len(self.basis_names)

    def __getinitargs__(self):
        return (self.basis_names, self.metric_matrix)

    @memoize_method
    def bits_and_sign(self, basis_indices):
        # assert no repetitions
        assert len(set(basis_indices)) == len(basis_indices)

        sorted_basis_indices = tuple(sorted(
                (bindex, num)
                for num, bindex in enumerate(basis_indices)))
        blade_permutation = [num for bindex, num in sorted_basis_indices]

        bits = 0
        for bi in basis_indices:
            bits |= 2**bi

        return bits, permutation_sign(blade_permutation)

    @property
    @memoize_method
    def is_orthogonal(self):
        return (self.metric_matrix - np.diag(np.diag(self.metric_matrix)) == 0).all()

    @property
    @memoize_method
    def is_euclidean(self):
        return (self.metric_matrix == np.eye(self.metric_matrix.shape[0])).all()

    def blade_bits_to_str(self, bits, outer_operator="^"):
        return outer_operator.join(
                    name
                    for bit_num, name in enumerate(self.basis_names)
                    if bits & (1 << bit_num))

    def __repr__(self):
        if self is get_euclidean_space(self.dimensions):
            return "Space(%d)" % self.dimensions
        elif self.is_euclidean:
            return "Space(%r)" % self.basis_names
        else:
            return "Space(%r, %r)" % (self.basis_names, self.metric_matrix)


@memoize
def get_euclidean_space(n):
    """Return the canonical *n*-dimensional Euclidean :class:`Space`.
    """
    return Space(n)

# }}}


# {{{ blade product weights

def _shared_metric_coeff(shared_bits, space):
    result = 1

    basis_idx = 0
    while shared_bits:
        bit = (1 << basis_idx)
        if shared_bits & bit:
            result = result * space.metric_matrix[basis_idx, basis_idx]
            shared_bits ^= bit

        basis_idx += 1

    return result


class _GAProduct(object):
    pass


class _OuterProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        return int(not a_bits & b_bits)

    orthogonal_blade_product_weight = generic_blade_product_weight


class _GeometricProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        raise NotImplementedError("geometric product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    def orthogonal_blade_product_weight(a_bits, b_bits, space):
        shared_bits = a_bits & b_bits

        if shared_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 1


class _InnerProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        raise NotImplementedError("inner product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    def orthogonal_blade_product_weight(a_bits, b_bits, space):
        shared_bits = a_bits & b_bits

        if shared_bits == a_bits or shared_bits == b_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _LeftContractionProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    def orthogonal_blade_product_weight(a_bits, b_bits, space):
        shared_bits = a_bits & b_bits

        if shared_bits == a_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _RightContractionProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    def orthogonal_blade_product_weight(a_bits, b_bits, space):
        shared_bits = a_bits & b_bits

        if shared_bits == b_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _ScalarProduct(_GAProduct):
    @staticmethod
    def generic_blade_product_weight(a_bits, b_bits, space):
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    def orthogonal_blade_product_weight(a_bits, b_bits, space):
        if a_bits == b_bits:
            return _shared_metric_coeff(a_bits, space)
        else:
            return 0

# }}}


# {{{ multivector

def _cast_or_ni(obj, space):
    if isinstance(obj, MultiVector):
        return obj
    else:
        return MultiVector(obj, space)


class MultiVector(object):
    r"""An immutable multivector type. Its implementation follows [DFM].
    It is pickleable, and not picky about what data is used as coefficients.
    It supports :class:`pymbolic.primitives.Expression` objects of course,
    but it can take just about any other scalar-ish coefficients.

    .. attribute:: data

        A mapping from a basis vector bitmap (indicating blades) to coefficients.
        (see [DFM], Chapter 19 for idea and rationale)

    .. attribute:: space

    See the following literature:

        [DFM] L. Dorst, D. Fontijne, and S. Mann, `Geometric Algebra for Computer
        Science: An Object-Oriented Approach to Geometry
        <https://books.google.com?isbn=0080553109>`_. Morgan Kaufmann, 2010.

        [HS] D. Hestenes and G. Sobczyk, `Clifford Algebra to Geometric Calculus: A
        Unified Language for Mathematics and Physics
        <https://books.google.com?isbn=9027725616>`_. Springer, 1987.

    The object behaves much like the corresponding
    :class:`sympy.galgebra.GA.MV` object in :mod:`sympy`, especially with
    respect to the supported operators:

    .. csv-table::
        :header: Operation, Result
        :widths: 10, 40

        ``A+B``,             Sum of multivectors
        ``A-B``,             Difference of multivectors
        ``A*B``,             Geometric product :math:`AB`
        ``A^B``,             Outer product :math:`A\wedge B` of multivectors
        ``A|B``,             Inner product :math:`A\cdot B` of multivectors
        ``A<<B``,            Left contraction :math:`A\lrcorner B` of multivectors
        ``A>>B``,            Right contraction :math:`A\llcorner B` of multivectors

    .. warning ::

        Many of the multiplicative operators bind more weakly than
        even *addition*. Python's operator precedence further does not
        match geometric algebra, which customarily evaluates outer, inner,
        and then geometric.

        In other words: Use parentheses everywhere.

    .. autoattribute:: mapper_method

    .. rubric:: More products

    .. automethod:: scalar_product
    .. automethod:: x
    .. automethod:: __pow__

    .. rubric:: Unary operators

    .. automethod:: inv
    .. automethod:: rev
    .. automethod:: invol
    .. automethod:: dual
    .. automethod:: __inv__
    .. automethod:: norm_squared
    .. automethod:: __abs__
    .. autoattribute:: I

    .. rubric:: Comparisons

    :class:`MultiVector` objects have a truth value corresponding to whether
    they have any blades with non-zero coefficients. They support testing
    for (exact) equality.

    .. automethod:: zap_near_zeros
    .. automethod:: close_to

    .. rubric:: Grade manipulation

    .. automethod:: gen_blades
    .. automethod:: project
    .. automethod:: xproject
    .. automethod:: all_grades
    .. automethod:: get_pure_grade
    .. automethod:: odd
    .. automethod:: even
    .. automethod:: project_min_grade
    .. automethod:: project_max_grade

    .. automethod:: as_scalar
    .. automethod:: as_vector

    .. rubric:: Helper functions

    .. automethod:: map

    """

    # {{{ construction

    def __init__(self, data, space=None):
        """
        :arg data: This may be one of the following:

            * a :class:`numpy.ndarray`, which will be turned into a grade-1
              multivector,
            * a mapping from tuples of basis indices (together indicating a blade,
              order matters and will be mapped to 'normalized' blades) to
              coefficients,
            * an array as described in :attr:`data`,
            * a scalar--where everything that doesn't fall into the above cases
              is viewed as a scalar.
        :arg space: A :class:`Space` instance. If *None* or an integer,
            :func:`get_euclidean_space` is called to obtain a default space with
            the right number of dimensions for *data*. Note: dimension guessing only
            works when a :class:`numpy.ndarray` is being passed for *data*.
        """

        dimensions = None

        if isinstance(data, np.ndarray):
            if len(data.shape) != 1:
                raise ValueError("only numpy vectors (not higher-rank objects) "
                        "are supported for 'data'")
            dimensions, = data.shape
            data = dict(
                    ((i,), xi) for i, xi in enumerate(data))
        elif isinstance(data, dict):
            pass
        else:
            data = {0: data}

        if space is None:
            space = get_euclidean_space(dimensions)
        else:
            if dimensions is not None and space.dimensions != dimensions:
                raise ValueError(
                        "dimension count of 'space' does not match that of 'data'")

        # {{{ normalize data to bitmaps, if needed

        from pytools import single_valued
        from pymbolic.primitives import is_zero
        if data and single_valued(isinstance(k, tuple) for k in six.iterkeys(data)):
            # data is in non-normalized non-bits tuple form
            new_data = {}
            for basis_indices, coeff in six.iteritems(data):
                bits, sign = space.bits_and_sign(basis_indices)
                new_coeff = new_data.setdefault(bits, 0) + sign*coeff

                if is_zero(new_coeff):
                    del new_data[bits]
                else:
                    new_data[bits] = new_coeff

            data = new_data

        # }}}

        # assert that multivectors don't get nested
        from pytools import any
        assert not any(isinstance(coeff, MultiVector)
                for coeff in six.itervalues(data))

        self.space = space
        self.data = data

    # }}}

    def __getinitargs__(self):
        return (self.data, self.space)

    mapper_method = "map_multivector"

    # {{{ stringification

    def stringify(self, coeff_stringifier, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_PRODUCT, PREC_SUM

        terms = []
        for bits in sorted(six.iterkeys(self.data),
                key=lambda bits: (bit_count(bits), bits)):
            coeff = self.data[bits]

            # {{{ try to find a stringifier

            strifier = None
            if coeff_stringifier is None:
                try:
                    strifier = coeff.stringifier()()
                except AttributeError:
                    pass
            else:
                strifier = coeff_stringifier

            # }}}

            if strifier is not None:
                if bits:
                    coeff_str = strifier(coeff, PREC_PRODUCT)
                else:
                    coeff_str = strifier(coeff, PREC_SUM)
            else:
                coeff_str = str(coeff)

            blade_str = self.space.blade_bits_to_str(bits)
            if bits:
                terms.append("%s*%s" % (coeff_str, blade_str))
            else:
                terms.append(coeff_str)

        if terms:
            result = " + ".join(terms)
        else:
            result = "0"

        return "MV(%s)" % result

    def __str__(self):
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.stringify(None, PREC_NONE)

    def __repr__(self):
        return "MultiVector(%s, %r)" % (self.data, self.space)

    # }}}

    # {{{ additive operators

    def __neg__(self):
        return MultiVector(
                dict((bits, -coeff)
                    for bits, coeff in six.iteritems(self.data)),
                self.space)

    def __add__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        if self.space is not other.space:
            raise ValueError("can only add multivectors from identical spaces")

        all_bits = set(six.iterkeys(self.data)) | set(six.iterkeys(other.data))

        from pymbolic.primitives import is_zero
        new_data = {}
        for bits in all_bits:
            new_coeff = self.data.get(bits, 0) + other.data.get(bits, 0)

            if not is_zero(new_coeff):
                new_data[bits] = new_coeff

        return MultiVector(new_data, self.space)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return other + (-self)

    # }}}

    # {{{ multiplicative operators

    def _generic_product(self, other, product_class):
        """
        :arg product_class: A subclass of :class:`_GAProduct`.
        """

        if self.space.is_orthogonal:
            bpw = product_class.orthogonal_blade_product_weight
        else:
            bpw = product_class.generic_blade_product_weight

        if self.space is not other.space:
            raise ValueError("can only compute products of multivectors "
                    "from identical spaces")

        from pymbolic.primitives import is_zero
        new_data = {}
        for sbits, scoeff in six.iteritems(self.data):
            for obits, ocoeff in six.iteritems(other.data):
                new_bits = sbits ^ obits
                weight = bpw(sbits, obits, self.space)

                if not is_zero(weight):
                    # These are nonzero by definition.
                    coeff = (weight
                            * canonical_reordering_sign(sbits, obits)
                            * scoeff * ocoeff)
                    new_coeff = new_data.setdefault(new_bits, 0) + coeff
                    if is_zero(new_coeff):
                        del new_data[new_bits]
                    else:
                        new_data[new_bits] = new_coeff

        return MultiVector(new_data, self.space)

    def __mul__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self._generic_product(other, _GeometricProduct)

    def __rmul__(self, other):
        return MultiVector(other, self.space) \
                ._generic_product(self, _GeometricProduct)

    def __xor__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self._generic_product(other, _OuterProduct)

    def __rxor__(self, other):
        return MultiVector(other, self.space) \
                ._generic_product(self, _OuterProduct)

    def __or__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self._generic_product(other, _InnerProduct)

    def __ror__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _InnerProduct)

    def __lshift__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self._generic_product(other, _LeftContractionProduct)

    def __rlshift__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _LeftContractionProduct)

    def __rshift__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self._generic_product(other, _RightContractionProduct)

    def __rrshift__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _RightContractionProduct)

    def scalar_product(self, other):
        r"""Return the scalar product, as a scalar, not a :class:`MultiVector`.

        Often written :math:`A*B`.
        """

        other_new = _cast_or_ni(other, self.space)
        if other_new is NotImplemented:
            raise NotImplementedError("scalar product between multivector and '%s'"
                    % type(other))

        return self._generic_product(other_new, _ScalarProduct).as_scalar()

    def x(self, other):
        r"""Return the commutator product.

        See (1.1.55) in [HS].

        Often written :math:`A\times B`.
        """
        return (self*other - other*self)/2

    def __pow__(self, other):
        """Return *self* to the integer power *other*."""

        other = int(other)

        from pymbolic.algorithm import integer_power
        return integer_power(self, other, one=MultiVector({0: 1}, self.space))

    def __truediv__(self, other):
        """Return ``self*(1/other)``.
        """
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self*other.inv()

    def __rtruediv__(self, other):
        """Return ``other * (1/self)``.
        """
        other = MultiVector(other, self.space)

        return other * self.inv()

    __div__ = __truediv__

    # }}}

    # {{{ unary operations

    def inv(self):
        """Return the *multiplicative inverse* of the blade *self*.

        Often written :math:`A^{-1}`.
        """

        nsqr = self.norm_squared()
        if len(self.data) == 0:
            raise ZeroDivisionError
        if len(self.data) > 1:
            if self.get_pure_grade() in [0, 1, self.space.dimensions]:
                return MultiVector(dict(
                    (bits, coeff/nsqr) for bits, coeff in six.iteritems(self.data)),
                    self.space)

            else:
                raise NotImplementedError("division by non-blades")

        (bits, coeff), = six.iteritems(self.data)

        # (1.1.54) in [HS]
        grade = bit_count(bits)
        if grade*(grade-1)//2 % 2:
            coeff = -coeff

        coeff = coeff/nsqr

        return MultiVector({bits: coeff}, self.space)

    def rev(self):
        r"""Return the *reverse* of *self*, i.e. the multivector obtained by
        reversing the order of all component blades.

        Often written :math:`A^\dagger`.
        """
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            grade = bit_count(bits)
            if grade*(grade-1)//2 % 2 == 0:
                new_data[bits] = coeff
            else:
                new_data[bits] = -coeff

        return MultiVector(new_data, self.space)

    def invol(self):
        r"""Return the grade involution (see Section 2.9.5 of [DFM]), i.e.
        all odd-grade blades have their signs flipped.

        Often written :math:`\widehat A`.
        """
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            grade = bit_count(bits)
            if grade % 2 == 0:
                new_data[bits] = coeff
            else:
                new_data[bits] = -coeff

        return MultiVector(new_data, self.space)

    def dual(self):
        r"""Return the dual of *self*, see (1.2.26) in [HS].

        Written :math:`\widetilde A` by [HS] and :math:`A^\ast` by [DFW].
        """

        return self | self.I.rev()

    def __inv__(self):
        """Return the dual of *self*, see :meth:`dual`."""
        return self.dual()

    def norm_squared(self):
        return self.rev().scalar_product(self)

    def __abs__(self):
        return self.norm_squared()**0.5

    @property
    def I(self):  # noqa
        """Return the pseudoscalar associated with this object's :class:`Space`.
        """
        return MultiVector({2**self.space.dimensions-1: 1}, self.space)

    # }}}

    # {{{ comparisons

    @memoize_method
    def __hash__(self):
        result = hash(self.space)
        for bits, coeff in six.iteritems(self.data):
            result ^= hash(bits) ^ hash(coeff)

        return result

    def __bool__(self):
        return bool(self.data)

    __nonzero__ = __bool__

    def __eq__(self, other):
        other = _cast_or_ni(other, self.space)
        if other is NotImplemented:
            return NotImplemented

        return self.data == other.data

    def __ne__(self, other):
        return not self.__eq__(other)

    def zap_near_zeros(self, tol=None):
        """Remove blades whose coefficient is close to zero
        relative to the norm of *self*.
        """

        if tol is None:
            tol = 1e-13

        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            if abs(coeff) > tol:
                new_data[bits] = coeff

        return MultiVector(new_data, self.space)

    def close_to(self, other, tol=None):
        return not (self-other).zap_near_zeros(tol=tol)

    # }}}

    # {{{ grade manipulation

    def gen_blades(self, grade=None):
        """Generate all blades in *self*, optionally only those of a specific
        *grade*.
        """

        if grade is None:
            for bits, coeff in six.iteritems(self.data):
                yield MultiVector({bits: coeff}, self.space)
        else:
            for bits, coeff in six.iteritems(self.data):
                if bit_count(bits) == grade:
                    yield MultiVector({bits: coeff}, self.space)

    def project(self, r):
        r"""Return a new multivector containing only the blades of grade *r*.

        Often written :math:`\langle A\rangle_r`.
        """
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            if bit_count(bits) == r:
                new_data[bits] = coeff

        return MultiVector(new_data, self.space)

    def xproject(self, r, dtype=None):
        r"""If ``r == 0``, return ``self.project(0).as_scalar()``.
        If ``r == 1``, return ``self.project(1).as_vector(dtype)``.
        Otherwise, return ``self.project(r)``.
        """
        if r == 0:
            return self.project(0).as_scalar()
        elif r == 1:
            return self.project(1).as_vector(dtype)
        else:
            return self.project(r)

    def all_grades(self):
        """Return a :class:`set` of grades occurring in *self*."""

        return set(bit_count(bits) for bits, coeff in six.iteritems(self.data))

    def get_pure_grade(self):
        """If *self* only has components of a single grade, return
        that as an integer. Otherwise, return *None*.
        """
        if not self.data:
            return 0

        result = None

        for bits, coeff in six.iteritems(self.data):
            grade = bit_count(bits)
            if result is None:
                result = grade
            elif result == grade:
                pass
            else:
                return None

        return result

    def odd(self):
        """Extract the odd-grade blades."""
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            if bit_count(bits) % 2:
                new_data[bits] = coeff

        return MultiVector(new_data, self.space)

    def even(self):
        """Extract the even-grade blades."""
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            if bit_count(bits) % 2 == 0:
                new_data[bits] = coeff

        return MultiVector(new_data, self.space)

    def project_min_grade(self):
        """
        .. versionadded:: 2014.2
        """

        return self.project(min(self.all_grades()))

    def project_max_grade(self):
        """
        .. versionadded:: 2014.2
        """

        return self.project(max(self.all_grades()))

    def as_scalar(self):
        result = 0
        for bits, coeff in six.iteritems(self.data):
            if bits != 0:
                raise ValueError("multivector is not a scalar")
            result = coeff

        return result

    def as_vector(self, dtype=None):
        """Return a :mod:`numpy` vector corresponding to the grade-1
        :class:`MultiVector` *self*.

        If *self* is not grade-1, :exc:`ValueError` is raised.
        """

        if dtype is not None:
            result = np.zeros(self.space.dimensions, dtype=dtype)
        else:
            result = [0] * self.space.dimensions

        log_table = dict((2**i, i) for i in range(self.space.dimensions))
        try:
            for bits, coeff in six.iteritems(self.data):
                result[log_table[bits]] = coeff
        except KeyError:
            raise ValueError("multivector is not a purely grade-1")

        if dtype is not None:
            return result
        else:
            return np.array(result)

    # }}}

    # {{{ helper functions

    def map(self, f):
        """Return a new :class:`MultiVector` with coefficients mapped by
        function *f*, which takes a single coefficient as input and returns the
        new coefficient.
        """
        new_data = {}
        for bits, coeff in six.iteritems(self.data):
            new_data[bits] = f(coeff)

        return MultiVector(new_data, self.space)

    # }}}

# }}}


def componentwise(f, expr):
    """Apply function *f* componentwise to object arrays and
    :class:`MultiVector` instances. *expr* is also allowed to
    be a scalar.
    """

    if isinstance(expr, MultiVector):
        return expr.map(f)

    from pytools.obj_array import with_object_array_or_scalar
    return with_object_array_or_scalar(f, expr)

# vim: foldmethod=marker
