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
were specified in each case with the addition of periods or sub_models. By default there is a phase called "default_0".
This has a volume of 1 and a time period of 1. When one of the two methods is used for the first time, it is extended
as shown below.

.. doctest::

    >>> from cobra2d.constraints.constraints import Constraints
    >>> con = Constraints()
    >>> print(con)
    +----------------------+-----------+
    | Sub-Model\Time Index |     0     |
    +----------------------+-----------+
    |           | id       | default_0 |
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
    |           | id       | default_0 | default_1 | default_2 | default_3 |
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
    |          | id        | leaf_0 |
    |    leaf  | volume    |   1    |
    |          | time      |   1    |
    +----------------------+--------+
    |          | id        | root_0 |
    |    root  | volume    |   2    |
    |          | time      |   1    |
    +----------------------+--------+

As we can see the default time period or sub_model is replaced as soon as we define times or sub_models ourselves.

Applying phase models and synchronizing gene rules
---------------------------------------------------

When :py:meth:`cobra2d.constraints.phase.Phases.apply_phases` receives a
reference model, ``link_genes=True`` synchronizes the gene-reaction rules of
the phase copies derived from that model. The same parameter is available on
:py:meth:`cobra2d.constraints.constraints.Constraints.apply_to_model`, which
forwards it.

A phase can instead use a manually assigned model through
:py:attr:`cobra2d.constraints.phase.Phase.model`. Such a model retains its own
reaction-specific gene rules. Cobra2D does not synchronize those rules across
phases because genes from independently supplied models cannot safely be
assumed to be equivalent. If ``link_genes=True`` is requested in this case, a
:py:class:`cobra2d.error.GenesNotLinked` warning lists the affected phase IDs.
Note that phases derived from the reference model are still linked in the same
call; the warning concerns only the manually assigned ones.

Gene IDs themselves are not phase-suffixed. Consequently, identical gene IDs
from different models may be represented by the same COBRApy
:py:class:`cobra.Gene` after merging, even though the gene-reaction rules on
the phase-specific reactions remain unchanged. Applications that require
cross-phase synchronization of manually assigned models must perform it
explicitly.

Adding new linker reactions
--------------------
.. autofunction:: cobra2d.constraints.constraints.Constraints.add_linker
.. autofunction:: cobra2d.constraints.constraints.Constraints.add_linker_series

Saving and loading
---------------------------------------------------

A constraints object can be written to an XML file and read back from it:

.. code-block:: python

    con.save_as_xml("conf.xml")
    con = Constraints.load_from_xml("conf.xml")

The format is defined by ``src/cobra2d/resources/schema.xsd``. A document
holds the phases, the transfers and the linkers, and declares the namespace
of that schema:

.. code-block:: xml

    <Conf xmlns="https://github.com/Toepfer-Lab/Cobra2D/blob/main/src/cobra2d/resources/schema.xsd">
        <phases>
            <phase id="leaf_0" light_dark="light" name="" objective_factor="1.0" timeframe="1" volume="1"/>
            <phase id="root_0" light_dark="light" name="" objective_factor="1.0" timeframe="1" volume="1"/>
        </phases>
        <transfers>
            <transfer metabolite_id="STARCH_p" lower_bound="0.0" upper_bound="1000.0">
                <destination refid="root_0"/>
                <source refid="leaf_0"/>
            </transfer>
        </transfers>
        <linkage/>
    </Conf>

What is stored are the phases with their reaction settings and the transfers
and linkers between them. A :py:class:`cobra.Model` assigned to a phase via
:py:attr:`cobra2d.constraints.phase.Phase.model` is not, and has to be
assigned again after loading.

Files written by Cobra2D 0.5.0 or earlier declare a different namespace and
are not supported.
