import logging
from difflib import get_close_matches

from cobra import Model
from ipywidgets import widgets, Text, Layout, Button, VBox, GridspecLayout

from model_duplication.visualization.converter import metexplore


def multi_checkbox_widget(descriptions):
    search_widget = Text()
    options_dict = {description: widgets.Checkbox(description=description,indent=False, value=False) for description in descriptions}
    options = [options_dict[description] for description in descriptions]
    options_widget = VBox(options,
                          layout=Layout(
                              overflow="hidden scroll",
                              height="auto",
                              max_height='250px',
                              margin = "0 0 0 0"
                          ))
    multi_select = GridspecLayout(4, 1)
    multi_select[0, 0] = search_widget
    multi_select[1:, 0] = options_widget

    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = [options_dict[description] for description in descriptions]
        else:
            # Filter by search field using difflib.
            close_matches = [v for v in descriptions if search_input in v]

            new_options = [options_dict[description] for description in close_matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names='value')
    return multi_select


def metexplore_select_groups(model: Model):
    groups = [group.id for group in model.groups]
    group_selection = multi_checkbox_widget(groups)

    def on_button_clicked(button):
        selected_options = [w.description for w in group_selection.children[1].children if w.value]

        metexplore(
            model=model,
            groups=selected_options,
        )

    button = Button(description="Open selected in MetExploreViz")
    button.on_click(on_button_clicked)

    grid = GridspecLayout(5, 1)
    grid[0:3, 0] = group_selection
    grid[4, 0] = button

    return grid
