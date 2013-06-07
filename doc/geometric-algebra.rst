Geometric Algebra
=================

.. automodule:: pymbolic.geometric_algebra

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
    .. automethod:: as_scalar
    .. automethod:: as_vector

    .. rubric:: Helper functions

    .. automethod:: map

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
    -1.85*e0 + 2.988*e1 + -5.2016*e2

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
    1
    >>> print one.I
    1*e0
    >>> print one.I ** 2
    -1.0

    >>> print (3+5j)*(2+3j)/(3j)
    (6.33333333333+3j)
    >>> print (3+5*one.I)*(2+3*one.I)/(3*one.I)
    6.33333333333 + 3.0*e0

The following test demonstrates the use of the object and shows many useful
properties:

.. literalinclude:: ../test/test_pymbolic.py
   :start-after: START_GA_TEST
   :end-before: END_GA_TEST

.. vim: sw=4
