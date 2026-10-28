Linker and transfer reactions
=============================================

This page describes how metabolites are transported between individual phases. As described in
:doc:`Structural design <structure>`, the temporal and spatial components are considered separately, so
metabolites can be moved either between time periods or between sub_models.

Spatial transport is represented by transfer reactions, temporal transport by linker reactions. The
corresponding classes behave almost identically and provide a similar interface.

.. _scaling:

=============================================
Scaling
=============================================

Phases can differ in the length of their time period (``timeframe``) and in
their ``volume``. Cobra2D takes this into account in the linker and transfer
reactions and in the objective. The bounds of the remaining reactions of a
phase are not scaled.

**Linker and transfer reactions:** The metabolite of the source phase has the
coefficient -1, and the metabolite of the destination phase has the
coefficient:

.. math::

    \frac{volume_{source} \cdot timeframe_{source}}
    {volume_{destination} \cdot timeframe_{destination}}

A linker or transfer is therefore only 1:1 if source and destination have the
same volume and timeframe. For example, in the quick start on the
:doc:`landing page <index>` the leaf has a volume of 2 and the root a volume
of 1, both with a timeframe of 12. The transfer of ``glc__D_e`` therefore
becomes ``glc__D_e_leaf_0 --> 2.0 glc__D_e_root_0``.

**Objective:** When the phases are applied to a model, the objective
coefficients of each phase are multiplied by
``objective_factor * timeframe * volume`` (see
:py:attr:`~cobra2d.constraints.phase.Phase.objective_factor`). In the quick
start, the biomass reaction of the leaf phases therefore has the coefficient
24 (1 * 12 * 2) and that of the root phases the coefficient 12 (1 * 12 * 1).

The weighted pFBA :py:func:`~cobra2d.optimization.parsimonious.adjusted_pfba`
also weights the flux of each reaction by ``timeframe * volume`` of its phase.

=============================================
Linker Reactions
=============================================

The Linker class is shown first, followed by the Linkage class, which manages multiple linkers.

.. autoclass:: cobra2d.constraints.linker::Linker
   :members:

.. autoclass:: cobra2d.constraints.linker::Linkage
   :members:

=============================================
Transfer Reactions
=============================================

Transfer reactions are handled in the same way as linker reactions. The Transfer class is shown first,
followed by the Transfers class, which manages multiple transfers.

.. autoclass:: cobra2d.constraints.transfer::Transfer
   :members:

.. autoclass:: cobra2d.constraints.transfer::Transfers
   :members:
