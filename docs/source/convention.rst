Naming Convention
=============================================


The following describes the naming convention used in this package. Cobra2D appends a phase suffix to the IDs of
all copied reactions, metabolites and groups (see :ref:`order-of-suffixes`). The only reactions it creates itself
are transfer and linker reactions, whose IDs are described below.

Both source and destination refer to phase IDs, which follow the
``<sub_model>_<time>`` pattern (e.g. ``leaf_1``). A sub_model may itself
contain underscores, so a phase ID is split on its *last* underscore; the
time period must therefore not contain one.

Transfer reactions:
----------------------
These reactions transport metabolites between sub_models, e.g. between cell types, tissues or organs (spatial transport).

ID: <Metabolite_ID>_tr_[<source_sub_model>|<destination_sub_model>]_<time>

**Example:**
    | Description: Transfer of starch from leaf to root
    | ID: STARCH_p_tr_[leaf|root]_1
    | STARCH_p_leaf_1 --> STARCH_p_root_1


Linker reactions:
--------------------
These reactions transport metabolites between time periods (temporal transport). Linker reactions usually run in one direction, from ``t`` to ``t+1``.

ID: <Metabolite_ID>_lk_<sub_model>_[<origin_time>|<destination_time>]

**Example:**
    | Description: Linker of starch in the leaf from time period 1 to 2
    | ID: STARCH_p_lk_leaf_[1|2]
    | STARCH_p_leaf_1 --> STARCH_p_leaf_2

.. note::
    The examples above show the reactions with a coefficient of 1 for both
    metabolites. This only applies if source and destination have the same
    volume and timeframe. Otherwise, the coefficient of the destination
    metabolite is scaled, see :ref:`scaling`.


.. _order-of-suffixes:

Order of suffixes:
-----------------------------------
IDs are built by appending suffixes to the original ID. Spatial subsystems come first, ordered from the smallest
to the largest, e.g. compartment, cell type, tissue, organ. The time period comes last. It is always present,
since every phase ID ends with one, even if no time periods were defined explicitly (e.g. ``default_0``).

The general structure is therefore:

ID: <item_id>_<sub_model>_<time>

Linker and transfer reactions deviate from this structure: since they act either across time or across space, they have to name two time periods or two sub_models as origin and destination.
