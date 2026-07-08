Naming Convention
=============================================


The following describes the nomenclature used in this package. Since we are only creating transfer and linker reactions, we only describe these.

Both source and destination refer to phase IDs, which follow the
``<sub_model>-<time>`` pattern (e.g. ``leaf-1``).

Transfer reactions:
----------------------
These are reactions that transport for example metabolites between cell types, tissues or organs (spatial transport).

ID: <Metabolite_ID>_tr_[<source_sub_model>|<destination_sub_model>]_<time>

**Example:**
    | Description: Transfer of starch from leaf to root
    | ID: STARCH_p_tr_[leaf|root]_1
    | STARCH_p_leaf-1 --> STARCH_p_root-1


Linker reactions:
--------------------
These are reactions that represent the transport of metabolites between time periods (temporal transport). Linker reactions are usually unidirectional from ``t`` to ``t+1``.

ID: <Metabolite_ID>_lk_<sub_model>_[<origin_time>|<destination_time>]

**Example:**
    | Description: Linker of starch in the leaf from time period 1 to 2
    | ID: STARCH_p_lk_leaf_[1|2]
    | STARCH_p_leaf-1 --> STARCH_p_leaf-2


Order of suffixes:
-----------------------------------
Here we present the structure on which the nomenclature is based.

Subsystems are listed by size, e.g. compartment, cell type, tissue, organ and so on.
These are followed by the time period if time periods are in use.

Therefore, the general result is :

ID: <item_id>_<sub_model>_<time>

Linker and transfer reactions deviate from this structure, as either 2 submodels or 2 time periods must be specified as origin and destination, since they only act either across a time or space.
