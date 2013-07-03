Primitives (Basic Objects)
==========================

.. automodule:: pymbolic.primitives

Expression base class
---------------------

.. autoclass:: Expression

    .. attribute:: attr

    .. attribute:: mapper_method

        The :class:`pymbolic.mapper.Mapper` method called for objects of
        this type.

    .. automethod:: stringifier

    .. automethod:: __eq__
    .. automethod:: __hash__
    .. automethod:: __str__
    .. automethod:: __repr__

Sums, products and such
-----------------------

.. autoclass:: Variable
    :undoc-members:
    :members: mapper_method

.. autoclass:: Call
    :undoc-members:
    :members: mapper_method

.. autoclass:: Subscript
    :undoc-members:
    :members: mapper_method

.. autoclass:: Lookup
    :undoc-members:
    :members: mapper_method

.. autoclass:: Sum
    :undoc-members:
    :members: mapper_method

.. autoclass:: Product
    :undoc-members:
    :members: mapper_method

.. autoclass:: Quotient
    :undoc-members:
    :members: mapper_method

.. autoclass:: FloorDiv
    :undoc-members:
    :members: mapper_method

.. autoclass:: Remainder
    :undoc-members:
    :members: mapper_method

.. autoclass:: Power
    :undoc-members:
    :members: mapper_method

Shift operators
---------------

.. autoclass:: LeftShift
    :undoc-members:
    :members: mapper_method

.. autoclass:: RightShift
    :undoc-members:
    :members: mapper_method

Bitwise operators
-----------------

.. autoclass:: BitwiseNot
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseOr
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseXor
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseAnd
    :undoc-members:
    :members: mapper_method

Comparisons and logic
---------------------

.. autoclass:: Comparison
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalNot
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalAnd
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalOr
    :undoc-members:
    :members: mapper_method

.. autoclass:: If
    :undoc-members:
    :members: mapper_method

Code generation helpers
-----------------------

.. autoclass:: CommonSubexpression
    :undoc-members:
    :members: mapper_method

.. autoclass:: cse_scope
.. autofunction:: make_common_subexpression

Helper functions
----------------

.. autofunction:: is_zero
.. autofunction:: is_constant
.. autofunction:: register_constant_class
.. autofunction:: unregister_constant_class
.. autofunction:: variables

Interaction with :mod:`numpy` arrays
------------------------------------

:mod:`numpy.ndarray` instances are supported anywhere in an expression.
In particular, :mod:`numpy` object arrays are useful for capturing
vectors and matrices of :mod:`pymbolic` objects.

.. autofunction:: make_sym_vector

.. vim: sw=4
