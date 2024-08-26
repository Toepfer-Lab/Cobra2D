Naming Convention
=============================================


The following describes the nomenclature used in this package. Since we are only creating transports and linkers, we only describe these.

Transfer reactions:
----------------------
These are reactions that transport for example metabolites between cells, tissues or organs.

ID: <Metabolite_ID>_tr_[<source_sub_model>|<destination_sub_model>]_<time>

**Example:**
    | Description: Transfer of starch from leaf to root
    | ID: STARCH_p_tr\_ [leaf|root]_1
    | STARCH_p_leaf_1 --> STARCH_p_root_1


Linker reactions:
--------------------
These are reactions that represent the transport of metabolites between time periods.

ID: <Metabolite_ID>_tr_[<source_sub_model>|<destination_sub_model>]_<time>

**Example:**
    | Description: Transfer of starch from leaf to root
    | ID: STARCH_p_tr\_ [leaf|root]_1
    | STARCH_p_leaf_1 --> STARCH_p_root_1


Order of suffixes:
-----------------------------------
Here we present the structure on which the nomenclature is based.

Subsystems are listed by size, e.g. compartment, cell type, tissue, organ and so on.
These are followed by the time period if time periods are in use.

Therefore, the general result is :

ID: <item_id>_<sub_model>_<time>

Linker and transfer reactions deviate from this structure, as either 2 submodels or 2 time periods must be specified as origin and destination.