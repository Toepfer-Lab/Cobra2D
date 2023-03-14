from re import sub
from typing import List, Optional

from cobra import Model, Solution, Metabolite
from ipywidgets import (
    widgets,
    Text,
    Layout,
    Button,
    VBox,
    GridspecLayout,
    HTML,
)

from cobra2d.visualization.converter import metexplore


def multi_checkbox_widget(descriptions):
    search_widget = Text()
    options_dict = {}
    options = []

    for description, selected in descriptions:
        widget = widgets.Checkbox(
            description=description, indent=False, value=selected
        )

        options_dict[description] = widget
        options.append(widget)

    options_widget = VBox(
        options,
        layout=Layout(
            overflow="hidden scroll",
            height="auto",
            max_height="250px",
            margin="0 0 0 0",
        ),
    )
    multi_select = GridspecLayout(4, 1)
    multi_select[0, 0] = search_widget
    multi_select[1:, 0] = options_widget

    def on_text_change(change):
        search_input = change["new"]
        if search_input == "":
            # Reset search field
            new_options = [
                options_dict[description] for description, _ in descriptions
            ]
        else:
            close_matches = [v for v, _ in descriptions if search_input in v]

            new_options = [
                options_dict[description] for description in close_matches
            ]

        options_widget.children = new_options

    search_widget.observe(on_text_change, names="value")
    return multi_select


def select_side_metabolites(
    model: Model, side_metabolites: Optional[List[str]] = None
):
    # ToDo read File

    metabolites = []
    if side_metabolites is None:
        side_metabolites = []

    metabolite: Metabolite
    for metabolite in model.metabolites:
        is_side_metabolite = metabolite.id in side_metabolites
        n_reactions = len(metabolite.reactions)

        metabolites.append(
            (
                f"{metabolite.id} ({n_reactions})",
                is_side_metabolite,
                n_reactions,
            )
        )

    metabolites = sorted(metabolites, key=lambda x: x[2], reverse=True)

    metabolites_without_n_reactions = [(m[0], m[1]) for m in metabolites]
    side_selection = multi_checkbox_widget(metabolites_without_n_reactions)

    return side_selection


def metexplore_interface(
    model: Model,
    solution: Optional[Solution] = None,
    side_metabolites: Optional[List[str]] = None,
    remove_unselected_groups=True,
):
    groups = [(group.id, False) for group in model.groups]
    group_selection = multi_checkbox_widget(groups)
    side_metabolite_selection = select_side_metabolites(
        model=model, side_metabolites=side_metabolites
    )

    def on_button_clicked(button):
        selected_groups = [
            w.description
            for w in group_selection.children[1].children
            if w.value
        ]

        selected_side_metabolites = [
            sub(r" (.*)$", "", w.description)
            for w in side_metabolite_selection.children[1].children
            if w.value
        ]

        metexplore(
            model=model,
            groups=selected_groups,
            solution=solution,
            side_metabolites=selected_side_metabolites,
            removeUnselectedGroups=remove_unselected_groups,
        )

    button = Button(description="Open selected in MetExploreViz")
    button.on_click(on_button_clicked)

    grid = GridspecLayout(10, 3)
    grid.layout = Layout(grid_gap="5px 5px", margin="0px 0px 0px 0px")
    grid[0, 0] = HTML("<h2> Groups</h2>")
    grid[1:8, 0] = group_selection
    grid[9, 0] = button
    grid[0, 2] = HTML("<h2> Side metabolites</h2>")
    grid[1:8, 2] = side_metabolite_selection

    return grid
