import json
import logging
from importlib.resources import open_text
from io import BytesIO
from pathlib import Path
from subprocess import Popen
from typing import Union, List, Set, Dict, Tuple, Optional
from zipfile import ZipFile

import igraph as ig
import networkx as nx
import requests
from cobra import Model, Metabolite, Reaction, Solution
from cobra.core import Group
from tqdm import tqdm

from cobra2d import resources

webserver_process: Popen


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


def _group2lists(
    group: Group,
) -> Tuple[Set[Metabolite], Set[Reaction], Set[Group]]:
    """
    Function that locates all elements belonging to a group.
    The potential types of elements are metabolites, reactions and groups.
    Hereby all potential elements are searched recursively and also
    elements which do not belong to the group itself but for example to a
    reaction or group of said group. This is continued recursively.

    Args:
        group: The Cobrapy group whose elements should be returned

    Returns: A triplet consisting of all metabolites, reactions and
        groups that have said association to the given group.
        The sequence is as follows: (Metabolites, Reactions, Groups).
    """

    logging.info(
        f"Create list of all metabolites, "
        f"reactions, groups contained in group {group.id}."
    )
    metabolites2use = set()
    reactions2use = set()
    groups2use = set()

    groups2use.add(group)

    for item in group.members:
        if isinstance(item, Metabolite):
            logging.info(
                f"Metabolite {item.id} is " f"included in group {group.id}."
            )
            metabolites2use.add(item)

        elif isinstance(item, Reaction):
            logging.info(
                f"Reaction {item.id} is " f"included in group {group.id}."
            )
            reactions2use.add(item)
            logging.info(
                f"The following metabolites are present "
                f"in reaction {item.id}.\n "
                f"{item.metabolites}"
            )
            metabolites2use.update(item.metabolites)

        else:
            logging.info(f"Group {group.id} contains another group {item.id}.")
            met, rec, gr = _group2lists(item)

            metabolites2use.update(met)
            reactions2use.update(rec)
            groups2use.update(gr)

    return metabolites2use, reactions2use, groups2use


def __create_and_append_links(
    reaction: Reaction,
    nodes2id: Dict,
    reversibility: bool,
    links: List[Dict[str, Union[str, bool]]],
):
    for metabolite, coeff in reaction.metabolites.items():
        reaction_id = nodes2id[reaction.id]
        metabolite_id = nodes2id[metabolite.id]

        if coeff > 0:
            logging.info(
                f"Create connection from {reaction.id} to "
                f"{metabolite.id}. With node IDs {reaction_id} "
                f"and {metabolite_id}. Reversibility "
                f"{reversibility} and with the direction 'out'."
            )

            links.append(
                {
                    "source": reaction_id,
                    "target": metabolite_id,
                    "interaction": "out",
                    "reversible": reversibility,
                    "id": f"{reaction.id} -- {metabolite.id}",
                }
            )
        else:
            logging.info(
                f"Create connection from {metabolite.id} to "
                f"{reaction.id}. With node IDs  {metabolite_id}"
                f"and {reaction_id}. Reversibility "
                f"{reversibility} and with the direction 'in'."
            )

            links.append(
                {
                    "source": metabolite_id,
                    "target": reaction_id,
                    "interaction": "in",
                    "reversible": reversibility,
                    "id": f"{metabolite.id} -- {reaction.id}",
                }
            )


def cobra2metexplore(
    model: Model,
    groups: Optional[Union[str, List[str]]] = None,
    side_metabolites: Optional[List[str]] = None,
    removeUnselectedGroups=False,
) -> str:
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
    links: List[Dict[str, Union[str, bool]]] = []
    nodes2id = {}
    id = 0

    if side_metabolites is None:
        side_metabolites = []

    # Determine the elements defined by means of the groups parameter.
    metabolites2use = set()
    reactions2use = set()
    groups2use = set()

    if isinstance(groups, str):
        groups = [groups]

    logging.info("Identifying all the components of the model to be used.")
    if groups is not None:
        for group in groups:
            met, rec, gr = _group2lists(model.groups.get_by_id(group))
            metabolites2use.update(met)
            reactions2use.update(rec)
            groups2use.update(gr)
    else:
        logging.info("No restrictions specified. Using the entire model.")
        metabolites2use = model.metabolites
        reactions2use = model.reactions
        groups2use = model.groups

    # Create the nodes for metabolites and reactions.
    if removeUnselectedGroups:
        for metabolite in metabolites2use:
            logging.info(
                f"Creating Node for Metabolite {metabolite.id}. "
                f"With node number {id}."
            )
            side_metabolite = False
            if metabolite.id in side_metabolites:
                side_metabolite = True

            nodes.append(
                {
                    "name": metabolite.name,
                    "id": metabolite.id,
                    "compartment": metabolite.compartment,
                    "biologicalType": "metabolite",
                    "pathways": [],
                    "isSideCompound": side_metabolite,
                }
            )

            nodes2id[metabolite.id] = id
            id += 1
    else:
        for metabolite in model.metabolites:
            logging.info(
                f"Creating Node for Metabolite {metabolite.id}. "
                f"With node number {id}."
            )
            side_metabolite = False
            if metabolite.id in side_metabolites:
                side_metabolite = True

            hidden = True
            metabolites2useIDs = [met.id for met in metabolites2use]

            if metabolite.id in metabolites2useIDs:
                hidden = False

            nodes.append(
                {
                    "name": metabolite.name,
                    "id": metabolite.id,
                    "dbIdentifier": metabolite.id,
                    "compartment": metabolite.compartment,
                    "biologicalType": "metabolite",
                    "pathways": [],
                    "hidden": hidden,
                    "isSideCompound": side_metabolite,
                }
            )

            nodes2id[metabolite.id] = id
            id += 1

    reaction: Reaction
    if removeUnselectedGroups:
        for reaction in reactions2use:
            logging.info(
                f"Creating Node for Metabolite {reaction.id}. "
                f"With node number {id}."
            )
            reversibility = reaction.reversibility
            compartments = list(reaction.compartments)

            nodes.append(
                {
                    "name": reaction.name,
                    "id": reaction.id,
                    "dbIdentifier": reaction.id,
                    "reactionReversibility": reversibility,
                    "biologicalType": "reaction",
                    "compartment": compartments,
                    "pathways": [],
                }
            )

            nodes2id[reaction.id] = id
            id += 1

            # Create the connections within the network.
            __create_and_append_links(
                reaction=reaction,
                nodes2id=nodes2id,
                reversibility=reversibility,
                links=links,
            )

    else:
        reactions2useIDs = [reaction.id for reaction in reactions2use]

        for reaction in model.reactions:
            logging.info(
                f"Creating Node for Metabolite {reaction.id}. "
                f"With node number {id}."
            )
            reversibility = reaction.reversibility
            compartments = list(reaction.compartments)

            hidden = True
            if reaction.id in reactions2useIDs:
                hidden = False

            nodes.append(
                {
                    "name": reaction.name,
                    "id": reaction.id,
                    "reactionReversibility": reversibility,
                    "biologicalType": "reaction",
                    "compartment": compartments,
                    "pathways": [],
                    "hidden": hidden,
                }
            )

            nodes2id[reaction.id] = id
            id += 1

            # Create the connections within the network.
            __create_and_append_links(
                reaction=reaction,
                nodes2id=nodes2id,
                reversibility=reversibility,
                links=links,
            )

    # Define all groups as pathway so that they can be interpreted
    # correctly by MetExplore.
    group_obj: Group
    for group_obj in groups2use:
        for member in group_obj.members:
            if isinstance(member, Reaction) or isinstance(member, Metabolite):
                logging.info(
                    f"Adding Node {member.id} to Pathway {group_obj.id}."
                )
                pos = nodes2id[member.id]
                node = nodes[pos]
                node["pathways"].append(group_obj.id)
                nodes[pos] = node

    # Add created nodes and connections to the dictionary and
    # return them as JSON string.
    dic["nodes"] = nodes
    dic["links"] = links

    return json.dumps(dic, indent=4)


def cobra2metexplore_flux_file(solution: Solution, file: Union[Path, str]):
    """
    Converts a cobra solution into a tsv that can be read by MetExploreViz
    to integrate Flux data into the visualization.

    Args:
        solution: The solution of the :py:class:`cobra.model`.
        file: A string or :py:class:`Path` containing the location and file
            name under which the tsv containing the flux values should be
            created.

    """
    if isinstance(file, str):
        file = Path(file)

    fluxes = solution.fluxes

    buffer = "reactionId\tflux_values\n"
    for id, flux_value in fluxes.items():
        flux_value = round(flux_value, 4)
        flux_value = str(flux_value).replace(".", ",")
        buffer += f"{id}\t{flux_value}\n"

    with open(file, "w") as out:
        out.write(buffer)

    logging.info(
        f"Create file with flux values for the usage with "
        f"MetExploreViz at location {file}."
    )


def cobra2metexplore_file(
    model: Model,
    file: Union[Path, str],
    groups: Optional[Union[str, List[str]]] = None,
    side_metabolites: Optional[List[str]] = None,
    removeUnselectedGroups=True,
):
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

    logging.info("")

    out = cobra2metexplore(
        model=model,
        groups=groups,
        side_metabolites=side_metabolites,
        removeUnselectedGroups=removeUnselectedGroups,
    )

    if isinstance(file, str):
        file = Path(file)

    file = file.with_suffix(".json")
    file.parent.mkdir(exist_ok=True)

    with open(file, "w") as out_file:
        out_file.write(out)

    logging.info(f"JSON representation stored at location '{file}'.")


def list2side_metabolite_file(
    side_metabolites: List[str], file: Union[Path, str]
):
    if isinstance(file, str):
        file = Path(file)

    file = file.with_suffix(".txt")
    file.parent.mkdir(exist_ok=True)

    with open(file, "w") as out_file:
        out_file.write("\n".join(side_metabolites))


def metexplore(
    model: Model,
    dir: Union[Path, str] = Path.cwd() / "MetExplore",
    solution: Solution = None,
    groups: Optional[Union[str, List[str]]] = None,
    side_metabolites: Optional[List[str]] = None,
    removeUnselectedGroups=True,
):
    """
    This function creates all the necessary files to visualize a cobra model
    using MetExploreViz. Furthermore, all data necessary for MetExploreViz
    will be downloaded if they do not already exist in the specified folder.
    Furthermore, a local web server is started, which makes all files in the
    specified folder available. This is accessible at '127.0.0.1' and is
    automatically stopped when the IPython kernel is stopped.

    A web browser is automatically opened and the created JSON file
    is read in. The flux values must be read in manually via the interface.

    Args:
        model: The Cobra model to be visualized.
        dir: The directory in which all files are to be created.
            By default, a MetExplore folder is created and used in the
            current working directory.
        solution: The Cobra Solution belonging to the model. If none is
            passed, the model is automatically optimized to obtain a solution.
        groups: The IDs of the groups of the Cobra model to be
            visualized. By default, the whole model is used.
    """
    import subprocess
    import webbrowser

    if isinstance(dir, str):
        dir = Path(dir)

    if side_metabolites is None:
        side_metabolites = [""]

    dir.mkdir(exist_ok=True)
    cobra2metexplore_file(
        model=model,
        file=dir / "model.json",
        groups=groups,
        side_metabolites=side_metabolites,
        removeUnselectedGroups=removeUnselectedGroups,
    )
    list2side_metabolite_file(
        side_metabolites, file=dir / "side_metabolites.txt"
    )

    if solution is None:
        logging.info("No solution passed. Calculating one.")
        solution = model.optimize()
    cobra2metexplore_flux_file(solution, dir / "model_flux.csv")

    if not (dir / "metExploreViz").exists():
        url = "http://metexplore.toulouse.inrae.fr/metexploreViz/doc/files/metExploreViz_3.2.zip"  # noqa: E501

        r = requests.get(url, stream=True, allow_redirects=True)

        total_size = int(r.headers.get("content-length", 0))
        block_size = 5 * 1024

        pbar = tqdm(
            total=total_size, unit_scale=True, unit="B", unit_divisor=1024
        )

        zip: BytesIO
        with BytesIO() as f:
            for data in r.iter_content(block_size):
                f.write(data)
                pbar.update(n=block_size)
            with ZipFile(f) as zip_file:
                zip_file.extractall(path=dir)

        index = Path(dir / "metExploreViz/index.html")
        index.rename(index.parent / "original_index.html")

        with open_text(resources, "index.html", encoding="UTF-8") as file:
            with open(dir / "metExploreViz/index.html", "w") as opened:
                opened.write(file.read())

    global webserver_process

    try:
        webserver_process.kill()
    except NameError:
        pass

    webserver_process = subprocess.Popen(
        [
            "python",
            "-m",
            "http.server",
            "8000",
            "--bind",
            "127.0.0.1",
            "--directory",
            dir,
        ]
    )
    webbrowser.open("http://127.0.0.1:8000/metExploreViz/index.html")
