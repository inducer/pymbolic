Mappers
=======

.. automodule:: pymbolic.mapper


More specialized mappers
------------------------

Converting to strings and code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pymbolic.mapper.stringifier

Mappers
*******

.. autoclass:: StringifyMapper

    .. automethod:: __call__

.. autoclass:: CSESplittingStringifyMapperMixin

.. automodule:: pymbolic.mapper.c_code

.. autoclass:: CCodeMapper

.. automodule:: pymbolic.mapper.graphviz

.. autoclass:: GraphvizMapper


Some minimal mathematics
^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pymbolic.mapper.evaluator

.. autoclass:: EvaluationMapper

.. automodule:: pymbolic.mapper.differentiator

.. autoclass:: DifferentiationMapper

.. automodule:: pymbolic.mapper.distributor

.. autoclass:: DistributeMapper

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
