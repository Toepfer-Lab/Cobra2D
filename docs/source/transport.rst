Linker and transfer reactions
=============================================

Here we discuss the possibilities of transporting metabolites between individual phases. As described in structural design, the temporal and spatial components are considered separately, so metabolites can be moved between time periods or between spatial locations.

We speak of transfer reactions when talking about spatial transport and of linker reactions when talking about temporal transport. Both are listed below.

Both classes behave almost identically and provide a similar interface.

=============================================
Linker Reactions
=============================================

The linker class is shown first, followed by the linkage class. The linkage class comprises several linker reactions.

.. autoclass:: cobra2d.constraints.linker::Linker
   :members:

.. autoclass:: cobra2d.constraints.linker::Linkage
   :members:

=============================================
Transfer Reactions
=============================================

Transfer reactions are handled in the same way as linker reactions.

So first the transfer class is displayed, followed by the transfers class, which manages several transfer reactions.

.. autoclass:: cobra2d.constraints.transfer::Transfer
   :members:

.. autoclass:: cobra2d.constraints.transfer::Transfers
   :members:
