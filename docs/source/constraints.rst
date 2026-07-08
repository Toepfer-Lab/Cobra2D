Constraints Class
=============================================

In the following we will take a closer look at the Constraints class. This is
the one that brings together all the functionalities of this package.
For a user it is therefore the most important class.

.. autoclass:: cobra2d.constraints.constraints::Constraints
   :members:

Adding new time periods or sub_models
-----------------------------------------
This class contains two functions to add periods or sub_models.

.. autofunction:: cobra2d.constraints.constraints.Constraints.add_sub_models

.. autofunction:: cobra2d.constraints.constraints.Constraints.add_time_slots

The functions create phase objects for the newly
added time period, sub_model combinations. For the creation of the phase objects the parameters are used, which
were specified in each case with the addition of periods or sub_models. By default there is a phase called "default-0".
This has a volume of 1 and a time period of 1. When one of the two methods is used for the first time, it is extended
as shown below.

.. doctest::

    >>> from cobra2d.constraints.constraints import Constraints
    >>> con = Constraints()
    >>> print(con)
    +----------------------+-----------+
    | Sub-Model\Time Index |     0     |
    +----------------------+-----------+
    |           | id       | default-0 |
    |  default  | volume   |     1     |
    |           | time     |     1     |
    +----------------------+-----------+

By adding time frames we get

.. doctest::

    >>> from cobra2d.constraints.constraints import Constraints
    >>> con = Constraints()
    >>> con.add_time_slots(4, 2)
    >>> print(con)
    +----------------------+-----------+-----------+-----------+-----------+
    | Sub-Model\Time Index |     0     |     1     |     2     |     3     |
    +----------------------+-----------+-----------+-----------+-----------+
    |           | id       | default-0 | default-1 | default-2 | default-3 |
    |  default  | volume   |     1     |     1     |     1     |     1     |
    |           | time     |     2     |     2     |     2     |     2     |
    +----------------------+-----------+-----------+-----------+-----------+


If we add sub_models instead we get the following:

.. doctest::

    >>> from cobra2d.constraints.constraints import Constraints
    >>> con = Constraints()
    >>> con.add_sub_models(["leaf", "root"], [1,2])
    >>> print(con)
    +----------------------+--------+
    | Sub-Model\Time Index |   0    |
    +----------------------+--------+
    |          | id        | leaf-0 |
    |    leaf  | volume    |   1    |
    |          | time      |   1    |
    +----------------------+--------+
    |          | id        | root-0 |
    |    root  | volume    |   2    |
    |          | time      |   1    |
    +----------------------+--------+

As we can see the default time period or sub_model is replaced as soon as we define times or sub_models ourselves.

Adding new linker
--------------------
.. autofunction:: cobra2d.constraints.constraints.Constraints.add_linker
.. autofunction:: cobra2d.constraints.constraints.Constraints.add_linker_series