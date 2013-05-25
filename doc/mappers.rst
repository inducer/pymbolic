Mappers
=======

.. automodule:: pymbolic.mapper

Basic dispatch
--------------

.. autoclass:: Mapper

    .. automethod:: __call__

    .. method:: rec(expr, *args, **kwargs)

        Identical to :meth:`__call__`, but intended for use in recursive dispatch
        in mapper methods.

    .. automethod:: handle_unsupported_expression

    .. rubric:: Handling objects that don't declare mapper methods

    In particular, this includes many non-subclasses of 
    :class:`pymbolic.primitives.Expression`.

    .. automethod:: map_foreign

    These are abstract methods for foreign objects that should be overridden
    in subclasses:

    .. method:: map_constant(expr, *args, **kwargs)

        Mapper method for constants.
        See :func:`pymbolic.primitives.register_constant_class`.

    .. method:: map_list(expr, *args, **kwargs)

    .. method:: map_tuple(expr, *args, **kwargs)

    .. method:: map_numpy_array(expr, *args, **kwargs)

Base classes for new mappers
----------------------------

.. autoclass:: CombineMapper

.. autoclass:: IdentityMapper

.. autoclass:: WalkMapper

.. autoclass:: CSECachingMapperMixin

More specialized mappers
------------------------

Converting to strings and code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pymbolic.mapper.stringifier

.. _prec-constants:

Precedence constants
********************

.. data:: PREC_CALL
.. data:: PREC_POWER
.. data:: PREC_UNARY
.. data:: PREC_PRODUCT
.. data:: PREC_SUM
.. data:: PREC_COMPARISON
.. data:: PREC_LOGICAL_AND
.. data:: PREC_LOGICAL_OR
.. data:: PREC_NONE

Mappers
*******

.. autoclass:: StringifyMapper

    .. automethod:: __call__

.. autoclass:: CSESplittingStringifyMapperMixin

.. automodule:: pymbolic.mapper.c_code

.. autoclass:: CCodeMapper

Some minimal mathematics
^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pymbolic.mapper.evaluator

.. autoclass:: EvaluationMapper

.. automodule:: pymbolic.mapper.differentiator

.. autoclass:: DifferentiationMapper

.. automodule:: pymbolic.mapper.expander

.. autoclass:: ExpandMapper

.. automodule:: pymbolic.mapper.collector

.. autoclass:: TermCollector

.. automodule:: pymbolic.mapper.constant_folder

.. autoclass:: ConstantFoldingMapper
.. autoclass:: CommutativeConstantFoldingMapper

Finding expression properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pymbolic.mapper.dependency

.. autoclass:: DependencyMapper

.. automodule:: pymbolic.mapper.flop_counter

.. autoclass:: FlopCounter

.. vim: sw=4
