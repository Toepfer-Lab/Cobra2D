Visualization options
=============================================

There are three visualization options. Two of them, based on GraphViz and Cytoscape, show the structure of the
phases and the connections between them. The third one uses MetExploreViz to give insight into COBRApy models.

The following code block is the basis for the visualizations on this page.

.. doctest:: Viz

    >>> from cobra2d import Constraints, Linker
    >>> con = Constraints()
    >>> con.add_sub_models(["root", "leaf", "stem"], [1, 2, 1])
    >>> con.add_time_slots(5, 2)
    >>> con.add_linker_series("ATP",last2first=False)
    >>> con.add_linker( Linker( "ADP", source="stem_3", destination="stem_4" ) )


GraphViz
----------
GraphViz creates a static image that can also be used outside of Jupyter Notebooks.

.. note::
    Rendering the graph requires the Graphviz system package. It is separate from the
    ``graphviz`` Python package and cannot be installed via pip; please refer to the
    `documentation of graphviz <https://graphviz.readthedocs.io/en/stable/manual.html>`_.
    If it is missing, :py:meth:`~cobra2d.constraints.constraints.Constraints.create_graph`
    issues a :py:class:`~cobra2d.error.GraphvizNotInstalled` warning.

The visualization can be created with the following command. It returns a ``graphviz.Digraph``,
which is displayed directly in a Jupyter Notebook.

.. doctest:: Viz

    >>> graph = con.create_graph()


.. figure:: ../../assets/media/GraphViz.png
   :scale: 50 %
   :alt: Example of visualization using GraphViz

   Example of a GraphViz visualization in which ATP is transported to each
   following time period and ADP is transported from ``stem_3`` to
   ``stem_4``.

Cytoscape shows the same structure as GraphViz, but interactively. It therefore provides much more information,
although only for the phase or connection the user has selected.

GraphViz is thus the better choice for images to be used outside of a Jupyter Notebook, while Cytoscape is
better suited for exploring the phases within a Jupyter Notebook.

Cytoscape
----------
Unlike GraphViz, the Cytoscape visualization is interactive. While it provides more detail, the user has to select
a phase or connection to display the additional information, which makes it less suitable as a static
representation.

Below is a brief example of this visualization.

.. doctest:: Viz

    >>> con.cytoscape()  # doctest: +SKIP

.. figure:: ../../assets/media/ConInteractive.gif
   :scale: 50 %
   :alt: Example of visualization using Cytoscape

   Example of an interactive Cytoscape visualization. Clicking on a phase or
   a connection shows its details below the graph.


MetExplore
------------

A COBRApy model can also be visualized using MetExploreViz. Since large models are slow to render, an interface
allows selecting the groups of the model to be displayed and the metabolites to be hidden as side metabolites.

The groups are listed in the order in which they appear in the model. The metabolites are sorted by the number of
reactions they participate in, which is shown in parentheses.

.. doctest:: Viz

    >>> from cobra.io import load_model
    >>> from cobra2d.visualization.helper import metexplore_interface
    >>> model = load_model("textbook")
    >>> metexplore_interface(model)  # doctest: +SKIP


.. figure:: ../../assets/media/MetExploreVizInterface.png
   :scale: 50 %
   :alt: Example of the MetExploreViz interface

   Interface for selecting groups and hiding metabolites before visualizing a
   COBRApy model with MetExploreViz.
