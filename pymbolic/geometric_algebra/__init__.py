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

import contextlib
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    Protocol,
    TypeVar,
    cast,
    overload,
)

import numpy as np
from typing_extensions import Self, deprecated, override

from pytools import memoize, memoize_method, obj_array
from pytools.obj_array import ObjectArray, ObjectArray1D, ShapeT

from pymbolic.primitives import expr_dataclass, is_zero


if TYPE_CHECKING:
    import optype.numpy as onp
    from numpy.typing import DTypeLike


__doc__ = r"""
See `Wikipedia <https://en.wikipedia.org/wiki/Geometric_algebra>`__ for an idea
of what this is.

.. versionadded:: 2013.2

Also see :ref:`ga-examples`.

.. _ga-conventions:

Conventions and known issues
----------------------------

The operators in this module historically follow the conventions of [DFM]
(Dorst, Fontijne and Mann, *Geometric Algebra for Computer Science*). Those
conventions have been shown to rest on shaky foundations; see in particular
Eric Lengyel's `Poor Foundations in Geometric Algebra
<https://terathon.com/blog/poor-foundations-ga.html>`__ for a detailed
critique. The affected operations, and their replacements in this module,
are:

- **Inner product.** Once a metric is given, there is exactly one extension
  of the metric's inner product on the basis vectors to the full exterior
  algebra, given for multivectors *A*, *B* by
  :math:`A\cdot B = \langle A\widetilde B\rangle_0` (equivalently,
  :math:`A^\top G B`, where :math:`G` is the metric extended to the full
  exterior algebra). It is a *scalar*, it vanishes for blades of different
  grade, and it induces the norm :math:`\lVert A\rVert^2 = A\cdot A`. Use
  :meth:`MultiVector.inner` for this product.

  The ``|`` operator implements [DFM]'s "inner product" instead, which can
  produce non-scalar results (making it an interior product, not an inner
  product) and which, for equal-grade *k*-blades, differs from the true
  inner product by a factor of :math:`(-1)^{k(k-1)/2}`.

- **Scalar product.** [DFM] defines a separate "scalar product" (see
  :meth:`MultiVector.scalar_product`) with a reversed Gram determinant. It
  is superfluous once the inner product is defined correctly, and is
  deprecated in favor of :meth:`MultiVector.inner`.

- **Contractions.** [DFM]'s left and right contractions (``<<`` and ``>>``)
  are interior products that, for equal-grade blades, reduce to the scalar
  product instead of the inner product. The corrected contractions, which
  do reduce to the inner product for equal-grade blades, are available as
  :meth:`MultiVector.left_contraction` and
  :meth:`MultiVector.right_contraction`. For a *k*-blade *A* and an *l*-blade
  *B* (with :math:`k \le l`), they are given by

  .. math::

     A\lrcorner B = \langle B\widetilde A\rangle_{l-k},
     \qquad
     B\llcorner A = \langle\widetilde A\, B\rangle_{l-k},

  extended to general multivectors blade-by-blade and by linearity. For a
  vector *a* and a blade *B*, the geometric product decomposes as
  :math:`aB = B\llcorner a + a\wedge B`.

  The Lengyel article also gives equivalent Hodge-dual definitions,
  :math:`A\lrcorner B = A_{\star}\vee B` and :math:`B\llcorner A =
  B\vee A^{\star}`, where the subscript/superscript star is the left (resp.
  right) Hodge dual and :math:`\vee` is the "antiwedge" product. The
  antiwedge is *not* wedge-like: it is Grassmann's regressive product,
  which adds antigrades (so an antiwedge of a *p*-blade and a *q*-blade
  has grade :math:`p+q-n`) and is defined via the complements,
  :math:`X\vee Y = \overline{\overline X \wedge \overline Y}`. It is not
  defined in the article itself; see, e.g., `Lengyel's RGA wiki
  <https://rigidgeometricalgebra.org/wiki/index.php?title=Exterior_products>`__.
  The two formulations are equivalent; the grade-extraction form above is
  self-contained, and it is the one implemented here.

- **Dual.** ``~`` and :meth:`MultiVector.dual` implement [DFM]'s
  "dualization mapping" :math:`A\, I^{-1}`. Its orientation is inconsistent
  with the exterior algebra complements (among other issues, it flips the
  sense of rotation of mixed-grade operators such as quaternions). The Hodge
  dual :math:`A^\star = \widetilde A\, I` (more generally, the right
  complement of :math:`GA`) is available as
  :meth:`MultiVector.hodge_dual`; for equal-grade blades *A*, *B* it
  satisfies the defining property of the Hodge star,
  :math:`A\wedge B^\star = (A\cdot B)\, I`.

:meth:`MultiVector.norm_squared` (and hence ``abs``) computes
:math:`A\cdot A`, i.e. the norm induced by the true inner product, and is
not affected by the above. The deprecated operators and methods remain
available and continue to follow [DFM] exactly.

Spaces
------

.. autoclass:: Space

.. autofunction:: get_euclidean_space

Multivectors
------------

.. class:: CoeffT

    A type variable for coefficients of :class:`MultiVector`. Requires some arithmetic.

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
    >>> print(-mv_a.I*(mv_a^mv_b))
    MV(
        e0 * -1.8499999999999999
        + e1 * 2.9879999999999995
        + e2 * -5.201600000000001)

The following example demonstrates the (metric) inner product
:meth:`MultiVector.inner` and the Hodge dual :meth:`MultiVector.hodge_dual`,
and how they differ from the deprecated [DFM]-convention operators (see
:ref:`ga-conventions`):

.. doctest::

    >>> import numpy as np
    >>> import pymbolic.geometric_algebra as ga
    >>> MV = ga.MultiVector
    >>>
    >>> a = MV(np.array([1, 2, 3]))
    >>> b = MV(np.array([4, 5, 6]))
    >>> B = a ^ b
    >>> print(a.inner(b))
    32
    >>> print(B.inner(B))
    54
    >>> print(B | B)
    MV(-54)
    >>> print(B.hodge_dual())
    MV(e0 * -3 + e1 * 6 + e2 * -3)

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
    >>> print(one)
    MV(1)
    >>> print(one.I)
    MV(e0 * 1)
    >>> print(one.I ** 2)
    MV(-1.0)

    >>> print((3+5j)*(2+3j)/(3j))
    (6.333333333333333+3j)
    >>> print((3+5*one.I)*(2+3*one.I)/(3*one.I))
    MV(
        6.333333333333333
        + e0 * 3.0)

The following test demonstrates the use of the object and shows many useful
properties:

.. literalinclude:: ../test/test_pymbolic.py
   :start-after: START_GA_TEST
   :end-before: END_GA_TEST
"""


class _HasArithmetic(Protocol):
    def __neg__(self) -> Self: ...
    def __abs__(self) -> Self: ...

    def __add__(self, other: Self, /) -> Self: ...
    def __radd__(self, other: int, /) -> Self: ...

    def __sub__(self, other: Self, /) -> Self: ...

    def __mul__(self, other: Self, /) -> Self: ...
    def __rmul__(self, other: int, /) -> Self: ...

    def __pow__(self, other: Self, /) -> Self: ...


CoeffT = TypeVar("CoeffT", bound=_HasArithmetic)


# {{{ helpers

def permutation_sign(p: Iterable[int]) -> int:
    """
    :returns: the sign of the permutation *p*.
    """
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


def canonical_reordering_sign(a_bits: int, b_bits: int) -> int:
    """Count the number of basis vector swaps required to
    get the combination of *a_bits* and *b_bits* into canonical order.

    Algorithm from figure 19.1 of [DFM2010]_ in :class:`MultiVector`.

    :arg a_bits: bitmap representing basis blade *a*.
    :arg b_bits: bitmap representing basis blade *b*.
    """

    a_bits = a_bits >> 1
    s = 0
    while a_bits:
        s = s + (a_bits & b_bits).bit_count()
        a_bits = a_bits >> 1

    if s & 1:
        return -1
    else:
        return 1

# }}}


# {{{ space

@dataclass(frozen=True, init=False)
class Space(Generic[CoeffT]):
    """
    .. autoattribute :: basis_names
    .. autoattribute :: metric_matrix

    .. autoproperty :: dimensions
    .. autoproperty :: is_orthogonal
    .. autoproperty :: is_euclidean

    .. automethod:: bits_and_sign
    .. automethod:: blade_bits_to_str
    """

    basis_names: Sequence[str]
    "A sequence of names of basis vectors."

    metric_matrix: onp.Array2D[np.generic]
    """
    A *(dims, dims)*-shaped matrix, whose *(i, j)*-th entry represents the
    inner product of basis vector *i* and basis vector *j*.
    """

    def __init__(self,
                 basis: Sequence[str] | int | None = None,
                 metric_matrix: onp.Array2D[np.generic] | None = None) -> None:
        """
        :arg basis: A sequence of names of basis vectors, or an integer (the
            number of dimensions) to use the default names ``e0`` through ``eN``.
        :arg metric_matrix: See :attr:`metric_matrix`. If *None*, the Euclidean
            metric is assumed.
        """

        if basis is None and metric_matrix is None:
            raise TypeError(
                "At least one of 'basis' and 'metric_matrix' must be given")

        from numbers import Integral
        if basis is None:
            assert metric_matrix is not None
            basis_names = [f"e{i}" for i in range(metric_matrix.shape[0])]
        elif isinstance(basis, Integral):
            basis_names = [f"e{i}" for i in range(basis)]
        else:
            assert not isinstance(basis, int)
            basis_names = list(basis)

        if metric_matrix is None:
            metric_matrix = np.eye(len(basis_names), dtype=object)

        if not (
                len(metric_matrix.shape) == 2
                and all(dim == len(basis_names) for dim in metric_matrix.shape)):
            raise ValueError(
                f"'metric_matrix' has the wrong shape: {metric_matrix.shape}")

        object.__setattr__(self, "basis_names", basis_names)
        object.__setattr__(self, "metric_matrix", metric_matrix)

    @property
    def dimensions(self) -> int:
        """The dimension of the space."""
        return len(self.basis_names)

    @memoize_method
    def bits_and_sign(self, basis_indices: Sequence[int]) -> tuple[int, int]:
        # assert no repetitions
        assert len(set(basis_indices)) == len(basis_indices)

        sorted_basis_indices = tuple(sorted(
                (bindex, num)
                for num, bindex in enumerate(basis_indices)))
        blade_permutation = [num for _, num in sorted_basis_indices]

        bits = 0
        for bi in basis_indices:
            bits |= 2**bi

        return bits, permutation_sign(blade_permutation)

    def __getitem__(self, idx: tuple[int, int]) -> CoeffT:
        i, j = idx
        return cast("CoeffT", self.metric_matrix[i, j])

    @property
    @memoize_method
    def is_orthogonal(self) -> bool:
        """*True* if the metric is orthogonal (i.e. diagonal)."""
        return (self.metric_matrix - np.diag(np.diag(self.metric_matrix)) == 0).all()

    @property
    @memoize_method
    def is_euclidean(self) -> bool:
        """*True* if the metric matrix corresponds to the Euclidean metric."""
        return (self.metric_matrix == np.eye(self.metric_matrix.shape[0])).all()

    def blade_bits_to_str(self, bits: int, outer_operator: str = "^") -> str:
        return outer_operator.join(
                    name
                    for bit_num, name in enumerate(self.basis_names)
                    if bits & (1 << bit_num))

    @override
    def __repr__(self) -> str:
        if self is get_euclidean_space(self.dimensions):
            return f"Space({self.dimensions})"

        elif self.is_euclidean:
            return f"Space({self.basis_names!r})"
        else:
            return f"Space({self.basis_names!r}, {self.metric_matrix!r})"


@memoize
def get_euclidean_space(n: int) -> Space[int]:
    """Return the canonical *n*-dimensional Euclidean :class:`Space`."""
    return Space[int](n)

# }}}


# {{{ blade product weights

def _shared_metric_coeff(shared_bits: int, space: Space[CoeffT]) -> CoeffT | Literal[1]:
    result = 1

    basis_idx = 0
    while shared_bits:
        bit = (1 << basis_idx)
        if shared_bits & bit:
            result = result * space[basis_idx, basis_idx]
            shared_bits ^= bit

        basis_idx += 1

    return result


class _GAProduct(ABC, Generic[CoeffT]):
    @staticmethod
    @abstractmethod
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        ...

    @staticmethod
    @abstractmethod
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        ...


class _OuterProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        return int(not a_bits & b_bits)

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        return int(not a_bits & b_bits)


class _GeometricProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        raise NotImplementedError("geometric product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        shared_bits = a_bits & b_bits

        if shared_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 1


class _InnerProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        raise NotImplementedError("inner product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        shared_bits = a_bits & b_bits

        if shared_bits in (a_bits, b_bits):
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _LeftContractionProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT | int:
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        shared_bits = a_bits & b_bits

        if shared_bits == a_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _RightContractionProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT:
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        shared_bits = a_bits & b_bits

        if shared_bits == b_bits:
            return _shared_metric_coeff(shared_bits, space)
        else:
            return 0


class _ScalarProduct(_GAProduct[CoeffT]):
    @staticmethod
    @override
    def generic_blade_product_weight(
                a_bits: int,
                b_bits: int,
                space: Space[CoeffT]
            ) -> CoeffT:
        raise NotImplementedError("contraction product for spaces "
                "with non-diagonal metric (i.e. non-orthogonal basis)")

    @staticmethod
    @override
    def orthogonal_blade_product_weight(
                a_bits: int, b_bits: int, space: Space[CoeffT]
            ) -> CoeffT | int:
        if a_bits == b_bits:
            return _shared_metric_coeff(a_bits, space)
        else:
            return 0

# }}}


# {{{ multivector

def _cast_to_mv(obj: int | CoeffT | MultiVector[CoeffT],
                space: Space[CoeffT]) -> MultiVector[CoeffT]:
    if isinstance(obj, MultiVector):
        return obj
    else:
        return MultiVector(obj, space)


@expr_dataclass(init=False, hash=False)
class MultiVector(Generic[CoeffT]):
    r"""An immutable multivector type. Its implementation follows [DFM];
    see :ref:`ga-conventions` for known issues with these conventions and
    for the recommended replacements.
    It is pickleable, and not picky about what data is used as coefficients.
    It supports :class:`pymbolic.primitives.ExpressionNode` objects of course,
    but it can take just about any other scalar-ish coefficients.

    .. autoattribute:: data

    .. autoattribute:: space

    See the following literature:

        [DFM] L. Dorst, D. Fontijne, and S. Mann, `Geometric Algebra for Computer
        Science: An Object-Oriented Approach to Geometry
        <https://books.google.com?isbn=0080553109>`__. Morgan Kaufmann, 2010.

        [HS] D. Hestenes and G. Sobczyk, `Clifford Algebra to Geometric Calculus: A
        Unified Language for Mathematics and Physics
        <https://books.google.com?isbn=9027725616>`__. Springer, 1987.

    The object behaves much like the corresponding :class:`galgebra.mv.Mv`
    object in :mod:`galgebra`, especially with respect to the supported
    operators:

    =================== ========================================================
    Operation           Result
    =================== ========================================================
    ``A+B``             Sum of multivectors
    ``A-B``             Difference of multivectors
    ``A*B``             Geometric product :math:`AB`
    ``A^B``             Outer product :math:`A\wedge B` of multivectors
    ``A|B``             [DFM]-convention "inner product" of multivectors
    ``A<<B``            [DFM]-convention left contraction
                        :math:`A\lrcorner B` (``_|``) of multivectors, also
                        read as ':math:`A` removed from :math:`B`'.
    ``A>>B``            [DFM]-convention right contraction
                        :math:`A\llcorner B` (``|_``) of multivectors, also
                        read as ':math:`A` without :math:`B`'.
    =================== ========================================================

    .. note::

        The ``|``, ``<<`` and ``>>`` operators follow the conventions of
        [DFM], which are deprecated (see :ref:`ga-conventions` for details).
        Prefer :meth:`inner`, :meth:`left_contraction`,
        :meth:`right_contraction` and :meth:`hodge_dual` instead.

    .. warning ::

        Many of the multiplicative operators bind more weakly than
        even *addition*. Python's operator precedence further does not
        match geometric algebra, which customarily evaluates outer, inner,
        and then geometric.

        In other words: Use parentheses everywhere.

    .. autoattribute:: mapper_method

    .. rubric:: More products

    .. automethod:: inner
    .. automethod:: left_contraction
    .. automethod:: right_contraction
    .. automethod:: scalar_product
    .. automethod:: x
    .. automethod:: __pow__

    .. rubric:: Unary operators

    .. automethod:: inv
    .. automethod:: rev
    .. automethod:: invol
    .. automethod:: hodge_dual
    .. automethod:: dual
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

    # This prevents mishaps with array arithmetic, and, additionally, helps
    # arraycontext recognize this as an array container.
    __array_ufunc__: ClassVar[None] = None

    data: Mapping[int, CoeffT]
    """A mapping from a basis vector bitmap (indicating blades) to coefficients.
    (see [DFM], Chapter 19 for idea and rationale)
    """

    space: Space[CoeffT]

    mapper_method: ClassVar[str] = "map_multivector"

    # {{{ construction

    def __init__(
                self,
                data: (Mapping[int, CoeffT | int]
                       | Mapping[tuple[int, ...], CoeffT | int]
                       | onp.Array1D[np.generic]
                       | ObjectArray1D[CoeffT]
                       | CoeffT
                       | int),
                space: Space[CoeffT] | None = None
            ) -> None:
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

        data_dict: Mapping[tuple[int, ...], CoeffT | int] | Mapping[int, CoeffT | int]
        if isinstance(data, (np.ndarray, ObjectArray)):
            if len(data.shape) != 1:
                raise ValueError(
                    "Only numpy vectors (not higher-rank objects) "
                    f"are supported for 'data': shape {data.shape}")

            dimensions, = cast("tuple[int]", data.shape)
            data_dict = {(i,): xi for i, xi in enumerate(data)}

            if space is None:
                space = cast("Space[CoeffT]", get_euclidean_space(dimensions))

            if space.dimensions != dimensions:
                raise ValueError(
                    "Dimension of 'space' does not match that of 'data': "
                    f"got {space.dimensions}d space but expected {dimensions}d")
        elif isinstance(data, Mapping):
            data_dict = data
        else:
            data_dict = {0: cast("CoeffT", data)}

        if space is None:
            raise ValueError("No 'space' provided")

        # {{{ normalize data to bitmaps, if needed

        from pytools import single_valued

        if data_dict and single_valued(isinstance(k, tuple) for k in data_dict):
            # data is in non-normalized non-bits tuple form
            new_data: dict[int, CoeffT | int] = {}
            for basis_indices, coeff in data_dict.items():
                assert isinstance(basis_indices, tuple)

                bits, sign = space.bits_and_sign(basis_indices)
                new_coeff = (
                    new_data.setdefault(bits, 0)
                    + sign*coeff)

                if is_zero(new_coeff):
                    del new_data[bits]
                else:
                    new_data[bits] = new_coeff
        else:
            new_data = cast("dict[int, CoeffT | int]", data_dict)

        # }}}

        # assert that multivectors don't get nested
        assert not any(isinstance(coeff, MultiVector) for coeff in new_data.values())

        object.__setattr__(self, "space", space)
        object.__setattr__(self, "data", new_data)

    # }}}

    # {{{ stringification

    def stringify(self,
                coeff_stringifier: Callable[[CoeffT, int], str] | None,
                enclosing_prec: int
            ) -> str:
        from pymbolic.mapper.stringifier import PREC_PRODUCT, PREC_SUM

        terms: list[str] = []
        for bits in sorted(self.data.keys(),
                key=lambda _bits: (_bits.bit_count(), _bits)):
            coeff = self.data[bits]

            # {{{ try to find a stringifier

            strifier = None
            if coeff_stringifier is None:
                with contextlib.suppress(AttributeError):
                    strifier = cast(
                                    "Callable[[CoeffT, int], str]",
                                    coeff.stringifier()())  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
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
                terms.append(f"{blade_str} * {coeff_str}")
            else:
                terms.append(coeff_str)

        if terms:
            if any(len(t) > 15 for t in terms):
                result = "\n    " + "\n    + ".join(terms)
            else:
                result = " + ".join(terms)
        else:
            result = "0"

        return f"MV({result})"

    @override
    def __str__(self) -> str:
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.stringify(None, PREC_NONE)

    @override
    def __repr__(self) -> str:
        return f"MultiVector({self.data}, {self.space!r})"

    # }}}

    # {{{ additive operators

    def __neg__(self) -> MultiVector[CoeffT]:
        return MultiVector(
                {bits: -coeff
                    for bits, coeff in self.data.items()},
                self.space)

    def __add__(self, other: Self | int | CoeffT) -> MultiVector[CoeffT]:
        other_c = _cast_to_mv(other, self.space)

        if self.space is not other_c.space:
            raise ValueError("can only add multivectors from identical spaces")

        all_bits = set(self.data.keys()) | set(other_c.data.keys())

        from pymbolic.primitives import is_zero
        new_data = {
            bits: new_coeff
            for bits in all_bits
            if not is_zero(
                    new_coeff := (self.data.get(bits, 0) + other_c.data.get(bits, 0)))
            }

        return MultiVector(new_data, self.space)

    def __radd__(self, other: Self | int | CoeffT):
        return self.__add__(other)

    def __sub__(self, other: Self | int | CoeffT):
        return self + (-other)

    def __rsub__(self, other: Self | int | CoeffT):
        return other + (-self)

    # }}}

    # {{{ multiplicative operators

    def _generic_product(self,
                    other: MultiVector[CoeffT],
                    product_class: type[_GAProduct[CoeffT]],
                ) -> Self:
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
        new_data: dict[int, CoeffT | int] = {}
        for sbits, scoeff in self.data.items():
            for obits, ocoeff in other.data.items():
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

        return type(self)(new_data, self.space)

    def __mul__(self, other: Self | int | CoeffT) -> Self:
        c_other = _cast_to_mv(other, self.space)

        return self._generic_product(c_other, _GeometricProduct)

    def __rmul__(self, other: int | CoeffT) -> Self:
        return type(self)(other, self.space) \
                ._generic_product(self, _GeometricProduct)

    def __xor__(self, other):
        other = _cast_to_mv(other, self.space)

        return self._generic_product(other, _OuterProduct)

    def __rxor__(self, other):
        return MultiVector(other, self.space) \
                ._generic_product(self, _OuterProduct)

    @deprecated(
        "'|' implements the [DFM]-convention inner product, which is "
        "deprecated. Use MultiVector.inner() for the (metric) inner product, "
        "or MultiVector.left_contraction()/MultiVector.right_contraction() "
        "for contractions. See the pymbolic.geometric_algebra documentation.")
    def __or__(self, other):
        """[DFM]-convention "inner product".

        .. deprecated:: 2025.1

            See :ref:`ga-conventions`. Use :meth:`inner`,
            :meth:`left_contraction` or :meth:`right_contraction` instead.
        """
        other = _cast_to_mv(other, self.space)

        return self._generic_product(other, _InnerProduct)

    @deprecated(
        "'|' implements the [DFM]-convention inner product, which is "
        "deprecated. Use MultiVector.inner() for the (metric) inner product, "
        "or MultiVector.left_contraction()/MultiVector.right_contraction() "
        "for contractions. See the pymbolic.geometric_algebra documentation.")
    def __ror__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _InnerProduct)

    @deprecated(
        "'<<' implements the [DFM]-convention left contraction, which is "
        "deprecated. Use MultiVector.left_contraction() instead (the two "
        "differ by a grade-dependent sign). See the "
        "pymbolic.geometric_algebra documentation.")
    def __lshift__(self, other):
        """[DFM]-convention left contraction.

        .. deprecated:: 2025.1

            See :ref:`ga-conventions`. Use :meth:`left_contraction` instead.
        """
        other = _cast_to_mv(other, self.space)

        return self._generic_product(other, _LeftContractionProduct)

    @deprecated(
        "'<<' implements the [DFM]-convention left contraction, which is "
        "deprecated. Use MultiVector.left_contraction() instead (the two "
        "differ by a grade-dependent sign). See the "
        "pymbolic.geometric_algebra documentation.")
    def __rlshift__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _LeftContractionProduct)

    @deprecated(
        "'>>' implements the [DFM]-convention right contraction, which is "
        "deprecated. Use MultiVector.right_contraction() instead (the two "
        "differ by a grade-dependent sign). See the "
        "pymbolic.geometric_algebra documentation.")
    def __rshift__(self, other):
        """[DFM]-convention right contraction.

        .. deprecated:: 2025.1

            See :ref:`ga-conventions`. Use :meth:`right_contraction` instead.
        """
        other = _cast_to_mv(other, self.space)

        return self._generic_product(other, _RightContractionProduct)

    @deprecated(
        "'>>' implements the [DFM]-convention right contraction, which is "
        "deprecated. Use MultiVector.right_contraction() instead (the two "
        "differ by a grade-dependent sign). See the "
        "pymbolic.geometric_algebra documentation.")
    def __rrshift__(self, other):
        return MultiVector(other, self.space)\
                ._generic_product(self, _RightContractionProduct)

    def inner(self, other) -> CoeffT | int:
        r"""Return the (metric) inner product :math:`A\cdot B`, as a scalar
        (not a :class:`MultiVector`).

        This is the unique extension of the inner product defined by
        :attr:`Space.metric_matrix` on the basis vectors to the full
        exterior algebra: for multivectors *A* and *B*,

        .. math::

            A\cdot B = \langle A\widetilde B\rangle_0
                      = \langle B\widetilde A\rangle_0.

        For blades in an orthogonal space it is the Gram determinant of the
        blade coefficients, and it vanishes unless the two blades have the
        same grade. In particular, :math:`A\cdot A` is the square of the
        norm induced by the metric (see :meth:`norm_squared`).

        .. note::

            The (deprecated) ``|`` operator does *not* implement this
            product; see :ref:`ga-conventions`. For a *k*-blade *A* in an
            orthogonal space, ``A | A`` equals :math:`(-1)^{k(k-1)/2}`
            times ``A.inner(A)``.

        .. versionadded:: 2025.1
        """

        other = _cast_to_mv(other, self.space)

        if self.space is not other.space:
            raise ValueError("can only compute inner products of multivectors "
                    "from identical spaces")

        if not self.space.is_orthogonal:
            raise NotImplementedError("inner product for spaces "
                    "with non-diagonal metric (i.e. non-orthogonal basis)")

        result: CoeffT | int = 0
        for bits, coeff in self.data.items():
            ocoeff = other.data.get(bits)
            if ocoeff is None:
                continue

            result = result \
                    + coeff * ocoeff * _shared_metric_coeff(bits, self.space)

        return result

    def left_contraction(self, other) -> MultiVector[CoeffT]:
        r"""Return the left contraction :math:`A\lrcorner B` of *self* with
        *other*.

        For blades, this is defined by

        .. math::

            A \lrcorner B
                = \langle B\widetilde A\rangle_{\mathrm{gr}\,B
                  - \mathrm{gr}\,A}

        (and zero if :math:`\mathrm{gr}\,A > \mathrm{gr}\,B`), and is
        extended to general multivectors blade-by-blade and by linearity.
        For blades of equal grade, the left contraction reduces to the
        inner product: :math:`A\lrcorner B = A\cdot B` (see :meth:`inner`).

        .. note::

            The (deprecated) ``<<`` operator implements the left
            contraction of [DFM], which differs from this one by a
            grade-dependent sign; see :ref:`ga-conventions`.

        .. versionadded:: 2025.1
        """

        other = _cast_to_mv(other, self.space)

        if self.space is not other.space:
            raise ValueError("can only compute products of multivectors "
                    "from identical spaces")

        if not self.space.is_orthogonal:
            raise NotImplementedError("contraction product for spaces "
                    "with non-diagonal metric (i.e. non-orthogonal basis)")

        from pymbolic.primitives import is_zero
        new_data: dict[int, CoeffT | int] = {}
        for abits, ac in self.data.items():
            a_grade = abits.bit_count()
            # A << B = <B Ã>_{grB-grA}
            rev_sign = -1 if (a_grade*(a_grade-1)//2) % 2 else 1

            for bbits, bc in other.data.items():
                # Nonzero only if supp(A) is contained in supp(B).
                if (abits | bbits) != bbits:
                    continue

                coeff = (rev_sign
                        * canonical_reordering_sign(bbits, abits)
                        * _shared_metric_coeff(abits, self.space)
                        * ac * bc)

                if not is_zero(coeff):
                    new_bits = bbits ^ abits
                    new_coeff = new_data.setdefault(new_bits, 0) + coeff
                    if is_zero(new_coeff):
                        del new_data[new_bits]
                    else:
                        new_data[new_bits] = new_coeff

        return type(self)(new_data, self.space)

    def right_contraction(self, other) -> MultiVector[CoeffT]:
        r"""Return the right contraction :math:`A\llcorner B` of *self* with
        *other*.

        For blades, this is defined by

        .. math::

            A \llcorner B
                = \langle\widetilde B\, A\rangle_{\mathrm{gr}\,A
                  - \mathrm{gr}\,B}

        (and zero if :math:`\mathrm{gr}\,A < \mathrm{gr}\,B`), and is
        extended to general multivectors blade-by-blade and by linearity.
        For blades of equal grade, the right contraction reduces to the
        inner product: :math:`A\llcorner B = A\cdot B` (see :meth:`inner`).
        In particular, for a vector *a* and a blade *B*, the geometric
        product decomposes as

        .. math::

            aB = B\llcorner a + a\wedge B.

        .. note::

            The (deprecated) ``>>`` operator implements the right
            contraction of [DFM], which differs from this one by a
            grade-dependent sign; see :ref:`ga-conventions`.

        .. versionadded:: 2025.1
        """

        other = _cast_to_mv(other, self.space)

        if self.space is not other.space:
            raise ValueError("can only compute products of multivectors "
                    "from identical spaces")

        if not self.space.is_orthogonal:
            raise NotImplementedError("contraction product for spaces "
                    "with non-diagonal metric (i.e. non-orthogonal basis)")

        from pymbolic.primitives import is_zero
        new_data: dict[int, CoeffT | int] = {}
        for abits, ac in self.data.items():
            for bbits, bc in other.data.items():
                # Nonzero only if supp(B) is contained in supp(A).
                if (abits | bbits) != abits:
                    continue

                b_grade = bbits.bit_count()
                # A >> B = <B̃ A>_{grA-grB}
                rev_sign = -1 if (b_grade*(b_grade-1)//2) % 2 else 1

                coeff = (rev_sign
                        * canonical_reordering_sign(bbits, abits)
                        * _shared_metric_coeff(bbits, self.space)
                        * ac * bc)

                if not is_zero(coeff):
                    new_bits = abits ^ bbits
                    new_coeff = new_data.setdefault(new_bits, 0) + coeff
                    if is_zero(new_coeff):
                        del new_data[new_bits]
                    else:
                        new_data[new_bits] = new_coeff

        return type(self)(new_data, self.space)

    @deprecated(
        "MultiVector.scalar_product() is deprecated. Use "
        "MultiVector.inner() instead (the [DFM] scalar product "
        "differs from the inner product for blades of grade 2 or 3 "
        "mod 4). See the pymbolic.geometric_algebra documentation.")
    def scalar_product(self, other) -> CoeffT | int:
        r"""Return the scalar product, as a scalar, not a :class:`MultiVector`.

        Often written :math:`A*B`.

        .. deprecated:: 2025.1

            The scalar product of [DFM] is a bilinear form that is separate
            from the (metric) inner product :meth:`inner`, and differs from
            it by a factor of :math:`(-1)^{k(k-1)/2}` for *k*-blades. It is
            superfluous once the inner product is defined correctly; see
            :ref:`ga-conventions`. Use :meth:`inner` instead.
        """
        other_new = _cast_to_mv(other, self.space)

        return self._generic_product(other_new, _ScalarProduct).as_scalar()

    def x(self, other):
        r"""Return the commutator product.

        See (1.1.55) in [HS].

        Often written :math:`A\times B`.
        """
        return (self*other - other*self)/2

    def __pow__(self, other: int):
        """Return *self* to the integer power *other*."""

        try:
            other = int(other)
        except ValueError:
            return NotImplemented

        from pymbolic.algorithm import integer_power
        return integer_power(
                             self,
                             other,
                             one=MultiVector[CoeffT]({0: 1}, self.space))

    def __truediv__(self, other):
        """Return ``self*(1/other)``.
        """
        other = _cast_to_mv(other, self.space)
        return self*other.inv()

    def __rtruediv__(self, other):
        """Return ``other * (1/self)``.
        """
        other = _cast_to_mv(other, self.space)
        return other * self.inv()

    __div__ = __truediv__

    # }}}

    # {{{ unary operations

    def inv(self) -> MultiVector[CoeffT]:
        """Return the *multiplicative inverse* of the blade *self*.

        Often written :math:`A^{-1}`.
        """

        nsqr = self.norm_squared()
        if len(self.data) == 0:
            raise ZeroDivisionError
        if len(self.data) > 1:
            if self.get_pure_grade() in [0, 1, self.space.dimensions]:
                return MultiVector({
                    bits:
                    # FIXME: Coefficients with division
                    coeff/nsqr  # pyright: ignore[reportOperatorIssue]
                        for bits, coeff in self.data.items()},
                    self.space)

            else:
                raise NotImplementedError("division by non-blades")

        (bits, coeff), = self.data.items()

        # (1.1.54) in [HS]
        grade = bits.bit_count()
        if grade*(grade-1)//2 % 2:
            coeff = -coeff

        # FIXME: Coefficients with division
        coeff = coeff/nsqr  # pyright: ignore[reportOperatorIssue]

        return MultiVector({bits: coeff}, self.space)

    def rev(self) -> MultiVector[CoeffT]:
        r"""Return the *reverse* of *self*, i.e. the multivector obtained by
        reversing the order of all component blades.

        Often written :math:`A^\dagger`.
        """
        new_data: dict[int, CoeffT] = {}
        for bits, coeff in self.data.items():
            grade = bits.bit_count()
            if grade*(grade-1)//2 % 2 == 0:
                new_data[bits] = coeff
            else:
                new_data[bits] = -coeff

        return MultiVector(new_data, self.space)

    def invol(self) -> MultiVector[CoeffT]:
        r"""Return the grade involution (see Section 2.9.5 of [DFM]), i.e.
        all odd-grade blades have their signs flipped.

        Often written :math:`\widehat A`.
        """
        new_data: dict[int, CoeffT] = {}
        for bits, coeff in self.data.items():
            grade = bits.bit_count()
            if grade % 2 == 0:
                new_data[bits] = coeff
            else:
                new_data[bits] = -coeff

        return MultiVector(new_data, self.space)

    def _ga4cs_dual(self) -> MultiVector[CoeffT]:
        """The [DFM]-convention dual ``self | self.I.rev()``
        (i.e. :math:`A I^{-1}`). See :meth:`dual`.
        """
        return self._generic_product(self.I.rev(), _InnerProduct)

    @deprecated(
        "MultiVector.dual() is deprecated. Use "
        "MultiVector.hodge_dual() instead (the [DFM] dualization "
        "mapping A*I**(-1) has an orientation that is inconsistent "
        "with the exterior algebra complements). See the "
        "pymbolic.geometric_algebra documentation.")
    def dual(self):
        r"""Return the dual of *self*, see (1.2.26) in [HS].

        Written :math:`\widetilde A` by [HS] and :math:`A^\ast` by [DFM].

        .. deprecated:: 2025.1

            This implements the "dualization mapping" of [DFM],
            :math:`A I^{-1}` (equivalently, ``self | self.I.rev()``). Its
            orientation is inconsistent with the exterior algebra
            complements, and it does not satisfy the defining property of
            the Hodge star. Use :meth:`hodge_dual` instead; see
            :ref:`ga-conventions`.
        """
        return self._ga4cs_dual()

    def hodge_dual(self) -> MultiVector[CoeffT]:
        r"""Return the Hodge dual :math:`A^\star` of *self*.

        For a nondegenerate orthogonal metric, this is given by

        .. math::

            A^\star = \widetilde A\, I,

        where :math:`I` is the pseudoscalar (see :attr:`I`); more
        generally, it is the right complement of :math:`GA`, where
        :math:`G` is the metric extended to the full exterior algebra. For
        blades *A*, *B* of equal grade, it satisfies the defining property
        of the Hodge star,

        .. math::

            A \wedge B^\star = (A\cdot B)\, I,

        and the Hodge dual of the pseudoscalar is the scalar given by the
        product of the diagonal entries of :attr:`Space.metric_matrix` (in
        particular, ``+1`` in a Euclidean space).

        .. note::

            This differs from the (deprecated) :meth:`dual`, which
            implements the dualization mapping of [DFM]; see
            :ref:`ga-conventions`.

        .. versionadded:: 2025.1
        """

        if not self.space.is_orthogonal:
            raise NotImplementedError("hodge dual for spaces "
                    "with non-diagonal metric (i.e. non-orthogonal basis)")

        return self.rev() * self.I

    def norm_squared(self) -> CoeffT | int:
        r"""Return the squared norm :math:`A\cdot A` of *self*, induced by
        the space's metric (see :meth:`inner`).
        """
        return self.inner(self)

    def __abs__(self) -> CoeffT | int:
        return self.norm_squared()**0.5

    @property
    def I(self):  # ruff:ignore[ambiguous-function-name, invalid-function-name]
        """Return the pseudoscalar associated with this object's :class:`Space`.
        """
        return MultiVector({2**self.space.dimensions-1: 1}, self.space)

    # }}}

    # {{{ comparisons

    @memoize_method
    def __hash__(self) -> int:
        result = hash(self.space)
        for bits, coeff in self.data.items():
            result ^= hash(bits) ^ hash(coeff)

        return result

    def __bool__(self) -> bool:
        return bool(self.data)

    def __eq__(self, other) -> bool:
        other = _cast_to_mv(other, self.space)

        return self.data == other.data

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def zap_near_zeros(self, tol: float | None = None) -> MultiVector[CoeffT]:
        """Remove blades whose coefficient is close to zero
        relative to the norm of *self*.
        """

        if tol is None:
            tol = 1e-12

        new_data = {
            bits: coeff
            for bits, coeff in self.data.items()
            # FIXME: coefficients with greater-than
            if abs(coeff) > tol  # pyright: ignore[reportOperatorIssue]
        }

        return MultiVector(new_data, self.space)

    def close_to(self, other, tol: float | None = None) -> bool:
        return not (self-other).zap_near_zeros(tol=tol)

    # }}}

    # {{{ grade manipulation

    def gen_blades(self, grade: int | None = None) -> Iterator[MultiVector[CoeffT]]:
        """Generate all blades in *self*, optionally only those of a specific
        *grade*.
        """

        if grade is None:
            for bits, coeff in self.data.items():
                yield MultiVector({bits: coeff}, self.space)
        else:
            for bits, coeff in self.data.items():
                if bits.bit_count() == grade:
                    yield MultiVector({bits: coeff}, self.space)

    def project(self, r: int) -> MultiVector[CoeffT]:
        r"""Return a new multivector containing only the blades of grade *r*.

        Often written :math:`\langle A\rangle_r`.
        """
        new_data: dict[int, CoeffT] = {
            bits: coeff
            for bits, coeff in self.data.items()
            if bits.bit_count() == r}

        return MultiVector(new_data, self.space)

    @overload
    # ignore because there most definitely is overlap.
    def xproject(self, r: Literal[0], dtype: DTypeLike = None) -> CoeffT | int: ...  # pyright: ignore[reportOverlappingOverload]

    @overload
    def xproject(self, r: Literal[1], dtype: DTypeLike = None) -> onp.Array1D[np.generic]: ...  # ruff:ignore[line-too-long]

    @overload
    def xproject(self, r: int, dtype: DTypeLike = None) -> MultiVector[CoeffT]: ...

    def xproject(
                self, r: int, dtype: DTypeLike = None
            ) -> int | CoeffT | onp.Array1D[np.generic] | MultiVector[CoeffT]:
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

    def all_grades(self) -> set[int]:
        """Return a :class:`set` of grades occurring in *self*."""

        return {bits.bit_count() for bits in self.data}

    def get_pure_grade(self) -> int | None:
        """If *self* only has components of a single grade, return
        that as an integer. Otherwise, return *None*.
        """
        if not self.data:
            return 0

        result = None

        for bits in self.data:
            grade = bits.bit_count()
            if result is None:
                result = grade
            elif result == grade:
                pass
            else:
                return None

        return result

    def odd(self) -> MultiVector[CoeffT]:
        """Extract the odd-grade blades."""
        new_data: dict[int, CoeffT] = {
            bits: coeff
            for bits, coeff in self.data.items()
            if bits.bit_count() % 2}

        return MultiVector(new_data, self.space)

    def even(self) -> MultiVector[CoeffT]:
        """Extract the even-grade blades."""
        new_data: dict[int, CoeffT] = {
            bits: coeff
            for bits, coeff in self.data.items()
            if bits.bit_count() % 2 == 0}

        return MultiVector(new_data, self.space)

    def project_min_grade(self) -> MultiVector[CoeffT]:
        """
        .. versionadded:: 2014.2
        """

        return self.project(min(self.all_grades()))

    def project_max_grade(self) -> MultiVector[CoeffT]:
        """
        .. versionadded:: 2014.2
        """

        return self.project(max(self.all_grades()))

    def as_scalar(self) -> CoeffT | int:
        result = 0
        for bits, coeff in self.data.items():
            if bits != 0:
                raise ValueError("multivector is not a scalar")
            result = coeff

        return result

    def as_vector(self,
                dtype: DTypeLike = None
            ) -> onp.Array1D[Any]:
        """Return a :mod:`numpy` vector corresponding to the grade-1
        :class:`MultiVector` *self*.

        If *self* is not grade-1, :exc:`ValueError` is raised.
        """
        if dtype is not None:
            # NOTE: this needs to be an ndarray from the beginning because we
            # can't do `np.array(result)` for object arrays and other things
            result = np.zeros(self.space.dimensions, dtype=dtype)
        else:
            result = [cast("CoeffT", 0)] * self.space.dimensions

        log_table = {2**i: i for i in range(self.space.dimensions)}
        try:
            for bits, coeff in self.data.items():
                result[log_table[bits]] = coeff
        except KeyError:
            raise ValueError("multivector is not a purely grade-1") from None

        return np.array(result) if isinstance(result, list) else result

    # }}}

    # {{{ helper functions

    def map(self, f: Callable[[CoeffT], CoeffT]) -> MultiVector[CoeffT]:
        """Return a new :class:`MultiVector` with coefficients mapped by
        function *f*, which takes a single coefficient as input and returns the
        new coefficient.
        """
        changed = False
        new_data: dict[int, CoeffT] = {}
        for bits, coeff in self.data.items():
            new_coeff = f(coeff)
            new_data[bits] = new_coeff
            if coeff is not new_coeff:
                changed = True

        if not changed:
            return self
        else:
            return MultiVector(new_data, self.space)

    # }}}

# }}}


@overload
def componentwise(
            f: Callable[[CoeffT], CoeffT],
            expr: CoeffT
        ) -> CoeffT: ...

@overload
def componentwise(
            f: Callable[[CoeffT], CoeffT],
            expr: MultiVector[CoeffT]
        ) -> MultiVector[CoeffT]: ...

@overload
def componentwise(
            f: Callable[[CoeffT], CoeffT],
            expr: ObjectArray[ShapeT, CoeffT]
        ) -> ObjectArray[ShapeT, CoeffT]: ...


def componentwise(
            f: Callable[[CoeffT], CoeffT],
            expr: CoeffT | MultiVector[CoeffT] | ObjectArray[ShapeT, CoeffT]
        ) -> CoeffT | MultiVector[CoeffT] | ObjectArray[ShapeT, CoeffT]:
    """Apply function *f* componentwise to object arrays and
    :class:`MultiVector` instances. *expr* is also allowed to
    be a scalar.
    """

    if isinstance(expr, MultiVector):
        return expr.map(f)

    return obj_array.vectorize(f, expr)

# vim: foldmethod=marker
