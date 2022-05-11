import json
from pathlib import Path
from typing import Union

import cobra.core
import igraph as ig
import networkx as nx
from cobra import Model, Metabolite, Reaction, Solution
from cobra.core import Group


def cobra2igraph(model: Model):
    g = ig.Graph()

    metabolite: Metabolite
    for metabolite in model.metabolites:
        g.add_vertex(name=metabolite.id, color="aliceblue")

    reaction: Reaction
    for reaction in model.reactions:
        g.add_vertex(name=reaction.id, color="darkmagenta")
        for metabolite, coeff in reaction.metabolites.items():
            # direction
            if coeff > 0:
                g.add_edge(
                    source=reaction.id, target=metabolite.id, coeff=coeff
                )
            else:
                g.add_edge(
                    source=metabolite.id, target=reaction.id, coeff=coeff
                )

    return g


def cobra2networkx(model: Model):
    graph = nx.DiGraph()

    for metabolite in model.metabolites:
        graph.add_node(metabolite.id, type="metabolite")

    for reaction in model.reactions:
        graph.add_node(reaction.id, type="reaction")
        for metabolite, coeff in reaction.metabolites.items():
            if coeff > 0:
                graph.add_edge(
                    reaction.id, metabolite.id, coeff=coeff, type="reaction"
                )
            else:
                graph.add_edge(
                    metabolite.id, reaction.id, coeff=-coeff, type="reaction"
                )

    return graph


def cobra2metexplore(model: Model) -> str:
    """
    It creates a JSON string that corresponds to the format that MetExploreViz
    needs to read in. It contains all reactions, metabolites and groups.
    The cobra groups are displayed in MetExploreViz as pathways.

    Note:
        Not all :py:class:`cobra.core.Group` have to correspond to pathways.
        Therefore, combinations of metabolites and reactions that do not
        correspond to any pathways may be displayed as pathways in
        MetExploreViz.

    Args:
        model: The :py:class:`cobra.model` to be translated into the
            JSON representation.

    Returns:
        The :py:class:`cobra.model` encoded in JSON.

    """
    dic = {}

    metabolite: Metabolite
    nodes = []
    links = []
    nodes2id = {}
    id = 0

    for metabolite in model.metabolites:
        nodes.append(
            {
                "name": metabolite.name,
                "id": metabolite.id,
                "compartment": metabolite.compartment,
                "biologicalType": "metabolite",
                "pathways": [],
            }
        )

        nodes2id[metabolite.id] = id
        id += 1

    reaction: Reaction
    for reaction in model.reactions:
        reversibility = reaction.reversibility
        compartments = list(reaction.compartments)

        nodes.append(
            {
                "name": reaction.name,
                "id": reaction.id,
                "reactionReversibility": reversibility,
                "biologicalType": "reaction",
                "compartment": compartments,
                "pathways": [],
            }
        )

        nodes2id[reaction.id] = id
        id += 1

        for metabolite, coeff in reaction.metabolites.items():
            if coeff > 0:
                links.append({
                    "source": nodes2id[reaction.id],
                    "target": nodes2id[metabolite.id],
                    "interaction": "out",
                    "reversible": reversibility,
                    "id": f"{reaction.id} -- {metabolite.id}"
                })
            else:
                links.append({
                    "source": nodes2id[metabolite.id],
                    "target": nodes2id[reaction.id],
                    "interaction": "in",
                    "reversible": reversibility,
                    "id": f"{metabolite.id} -- {reaction.id}"
                })

    group: Group
    for group in model.groups:
        for member in group.members:
            if isinstance(member, Reaction) or isinstance(member, Metabolite):
                pos = nodes2id[member.id]
                node = nodes[pos]
                node["pathways"].append(group.id)
                nodes[pos] = node

    dic["nodes"] = nodes
    dic["links"] = links

    return json.dumps(dic, indent=4)


def cobra2metexplore_flux_file(solution: Solution, file: Union[Path, str]):
    """
    Converts a cobra solution into a tsv that can be read by MetExploreViz
    to integrate Flux data into the visualization.

    Args:
        solution: The solution of the :py:class:`cobra.model`.
        file: A string or :py:class:`Path` containing the location and file name
            under which the tsv containing the flux values should be created.

    """
    if isinstance(file, str):
        file = Path(file)

    fluxes = solution.fluxes

    buffer = ("Identifier\tflux_values\n")
    for id, flux_value in fluxes.items():
        flux_value = round(flux_value, 4)
        flux_value = str(flux_value).replace('.', ',')
        buffer += f"{id}\t{flux_value}\n"

    with open(file, "w") as out:
        out.write(buffer)


def cobra2metexplore_file(model: Model, file: Union[Path, str]):
    """
    Function that creates a JSON file corresponding to a
    :py:class:`cobra.model` that can be read by MetExploreViz.

    The created file contains the information of the :py:class:`cobra.model`
    regarding all metabolites, reactions and groups.

    Note:
        The groups in the :py:class:`cobra.model` are displayed as pathways in
        MetExploreViz. However, the :py:class:`cobra.core.Group` do not
        necessarily correspond to pathways.

    Args:
        model: The :py:class:`cobra.model` to be translated into the
            JSON representation.

    Returns:
        The :py:class:`cobra.model` encoded in JSON.

    """
    out = cobra2metexplore(model)
    if isinstance(file, str):
        file = Path(file)

    file = file.with_suffix(".json")
    file.parent.mkdir(exist_ok=True)

    with open(file, "w") as out_file:
        out_file.write(out)
