Structural design
=============================================

Cobra2D breaks down a time and space resolved model into a spatial and a temporal component. A combination of
these two components for a single time and space is described as a phase. The entirety of these phases is
summarized by a constraints object.

The following is a brief description of the Constraints class and the phase class.

=============================================
Constraints Class
=============================================

In the following we will take a closer look at the Constraints class. This is
the one that brings together all the functionalities of this package.
For a user it is therefore the most important class.

.. autoclass:: cobra2d.constraints.constraints::Constraints
   :members:

To add periods or sub_models, 'add_sub_models' or 'add_time_slots' can be used.

These methods create all the necessary phase objects, taking into account the specified parameters.

=============================================
Phase Class
=============================================

As already described, a phase here defines the combination of a point in time and a defined spatial environment.

Multiple phases can be grouped into a Phases object, which simplifies the handling and application to a cobra model of these, as well as allowing a simple tabular representation.

.. autoclass:: cobra2d.constraints.phase::Phase
   :members:


.. autoclass:: cobra2d.constraints.phase::Phases
   :members:
