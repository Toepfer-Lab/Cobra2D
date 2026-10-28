Structural design
=============================================

Cobra2D decomposes a time- and space-resolved model into spatial and temporal components. The combination of a
single time period and a single sub_model is called a phase. A Constraints object holds all phases and
the linker and transfer reactions that connect them.

The following briefly describes the Constraints class and the Phase class.

=============================================
Constraints Class
=============================================

The Constraints class brings together all the functionality of this package,
which makes it the most important class for users.

Time periods are added with ``add_time_slots`` and sub_models with ``add_sub_models``.
Both methods create the required phase objects from the specified parameters.

The class, including its full API, is described on the
:doc:`Constraints class <constraints>` page.

=============================================
Phase Class
=============================================

As described above, a phase is the combination of a time period and a sub_model.

Multiple phases can be grouped into a Phases object, which makes it easy to apply them to a COBRApy model and to
display them as a table.

.. autoclass:: cobra2d.constraints.phase::Phase
   :members:


.. autoclass:: cobra2d.constraints.phase::Phases
   :members:
