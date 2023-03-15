"""
Implementation of the Constraints class.
"""
from __future__ import annotations

import warnings
from collections import OrderedDict
from importlib.resources import open_text
from inspect import isclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Tuple, Union, TextIO, Optional, Dict
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import ipycytoscape
import networkx as nx
from IPython.display import display
from cobra import Model, Reaction
from graphviz import Digraph
from ipywidgets import Output, HTML, Tab
from prettytable import PrettyTable
from rich.console import Console
from rich.table import Table
from typing_extensions import Literal
from xmlschema import XMLSchema

from cobra2d import resources
from cobra2d.constraints.linker import Linkage, Linker
from cobra2d.constraints.phase import Phase, Phases
from cobra2d.constraints.transfer import Transfers, Transfer
from cobra2d.error import InvalidLabel, PhaseNotFound
from cobra2d.utils import Matrix
from cobra2d.visualization.helper import metexplore_interface


class Constraints:
    """
    This class bundles the functionalities of :py:class:`Linker` and
    :py:class:`Linkage`. So the application of these is not only possible with
    a single line but there are also helper functions to simplify the creation
    of organs and time periods. Last but not least it realizes a storage of a
    constraints object as XML and also the creation of a constraints object
    based on such an XML file.

    Attributes:
        phases(Phases) :
        linker(Linkage) :
        transfers(Transfers):
    """

    def __init__(self):
        """
        Create a Constraints object.

        """
        self.phases = Phases()
        self.linker = Linkage()
        self.transfers = Transfers()
        self.order = Matrix()
        self.phases.add_phase(
            Phase(id="default-0", name="Default Phase", light_dark="light")
        )

        self.default_time = True
        self.default_sub_model = True

        self.time_ranges: List[Tuple[int, int, Literal["light", "dark"]]] = [
            (0, 1, "light")
        ]
        self.index_time_ranges = 0

        self.sub_models: List[Tuple[str, int, str]] = [
            ("default", 1, "Default sub_model")
        ]

    def __get_label_time(
        self, reverse: bool = False
    ) -> Tuple[List[str], List[int]]:
        labels: List[str] = []
        times: List[int] = []

        for phase in self.phases.phases:
            label_time = phase.id.split("-")

            labels.append(label_time[0])
            times.append(int(label_time[1]))

        labels = list(set(labels))
        times = list(set(times))

        labels.sort()
        times.sort(reverse=reverse)

        return labels, times

    def __str__(self):
        """
        The toString method of the Constraints class. It creates a tabular
        based representation with focus on the Phases.

        Returns:
            A table containing the IDs of the phases, their volume and time
            range.
        """

        labels, times = self.__get_label_time()

        output = PrettyTable(["Sub-Model\\Time Index"] + times)
        for label in labels:
            row = [
                " " * (len(label) - 2) + "| id\n"
                f"{label}  | volume\n" + (" " * len(label)) + "| time"
            ]

            for time in times:
                phase_id = f"{label}-{time}"
                phase = self.get_phase_by_id(phase_id)

                row.append(
                    f"{phase_id}\n" f"{phase.volume}\n" f"{phase.timeframe}"
                )

            output.add_row(row)
            output.hrules = 1

        return output.get_string()

    def get_phase_by_id(self, id: str) -> Phase:
        """
        A method to get individual phases by their ID.

        Args:
            id: ID of the desired phase.

        Returns:
            The phase that has the specified ID.
        """
        try:
            phase = self.phases.phases.get_by_id(id)
        except KeyError as e:
            raise PhaseNotFound from e

        return phase

    def add_reaction_to_phase(
        self,
        reaction: Reaction,
        phase: Union[str, Phase, List[str], List[Phase]],
    ):
        """
        A method that allows to influence the reaction in certain phases.
        For example, reactions during certain phases can be restricted by
        adjusting upper_bounds and lower_bounds.

        Args:
            reaction: A reaction that has the same ID as the one to be adjusted
                and contains the adjusted parameters. The ID must be the same
                as the original ID and must not have the phase name extension.
            phase: The ID of the phase, the phase itself or a list of IDs or a
                list of phases in which the adjustment defined by the reaction
                is to be performed.

        """

        if isinstance(phase, List):
            for single_phase in phase:
                self.add_reaction_to_phase(reaction, single_phase)
                return

        if isinstance(phase, str):
            phase = self.phases.phases.get_by_id(phase)

        assert isinstance(phase, Phase)
        phase.add_reaction(reaction)

    def rich_output(self):
        """
        Experimental only
        Display via rich
        """
        output = Table()

        output.add_column("Sub-Model\\Time Index")
        output.add_column(str(time[0] for time in self.time_ranges))

        for label, volume, name in self.sub_models:
            row = [
                " " * len(label) + " label\n"
                f"{label} {{ volume\n" + (" " * len(label)) + " time"
            ]
            for index, timeframe, light in self.time_ranges:
                row.append(f"{label}-{index}\n" f"{volume}\n" f"{timeframe}")

            output.add_row(*row)

        console = Console()
        console.print(output)

    def add_time_slots(
        self,
        n_ranges: int,
        time: int,
        light_dark: Literal["light", "dark"] = "light",
    ):
        """
        Method to add new time ranges. It is designed to create multiple time
        ranges of the same length that are also subject to the same
        :py:attr:`light_dark` parameter.

        Args:
            n_ranges: The number of how many such time ranges should be
                created.
            time: The length of the time ranges to be created.
            light_dark: The light_dark parameter to be assigned to these time
                ranges.

        """

        if self.default_time:
            self.default_time = False
            del self.time_ranges[0]
            self.phases.clear_phases()

        for i in range(n_ranges):
            i += self.index_time_ranges

            for label, volume, name in self.sub_models:
                self.phases.add_phase(
                    Phase(
                        id=f"{label}-{i}",
                        volume=volume,
                        name=name or "",
                        light_dark=light_dark,
                        timeframe=time,
                    )
                )

            self.time_ranges.append((i, time, light_dark))

        self.index_time_ranges += n_ranges

    def add_sub_models(
        self,
        labels: List[str],
        volumes: List[int],
        names: Union[List[str], None] = None,
    ):
        """
        Method to add sub models. These can correspond to organs, for example.

        Args:
            labels: A list containing the name of the sub models.
            volumes: A list containing the volumes of the sub models
            names: A list of human-readable names to be used for the sub
                models.

        """
        assert (len(labels) == len(volumes) and names is None) or (
            len(labels) == len(volumes) == len(names)  # type: ignore
        )

        if "default" in labels:
            raise InvalidLabel(
                "'default' is invalid as label. Please use another term."
            )

        if self.default_sub_model:
            self.default_sub_model = False
            del self.sub_models[0]
            self.phases.clear_phases()

        for label, volume, name in zip_longest(labels, volumes, names or ""):
            for index, timeframe, light_dark in self.time_ranges:
                self.phases.add_phase(
                    Phase(
                        id=f"{label}-{index}",
                        volume=volume,
                        name=name or "",
                        light_dark=light_dark,
                        timeframe=timeframe,
                    )
                )

            self.sub_models.append((label, volume, name))

    def remove_sub_model(self, id: str):
        raise NotImplementedError

    def add_linker(self, linker: Linker):
        """
        Method to add previously created linkers to the constraints object.

        Args:
            linker: The linker to be added.

        """

        try:
            self.get_phase_by_id(linker.destination)
        except PhaseNotFound as e:
            raise PhaseNotFound(
                f"The destination: '{linker.destination}' is unknown."
            ) from e

        try:
            self.get_phase_by_id(linker.source)
        except PhaseNotFound as e:
            raise PhaseNotFound(
                f"The source: '{linker.source}' is unknown."
            ) from e

        with warnings.catch_warnings(record=True) as w:
            self.linker.append(linker)
        for warning in w:
            warnings.warn(
                message=warning.message,
                category=warning.category,
                stacklevel=2,
                source=warning.source,
            )

    def add_transfer(self, transfer: Transfer):
        try:
            self.get_phase_by_id(transfer.destination)
        except PhaseNotFound as e:
            raise PhaseNotFound(
                f"The destination: '{transfer.destination}' is unknown."
            ) from e

        try:
            self.get_phase_by_id(transfer.source)
        except PhaseNotFound as e:
            raise PhaseNotFound(
                f"The source: '{transfer.source}' is unknown."
            ) from e

        with warnings.catch_warnings(record=True) as w:
            self.transfers.append(transfer)
        for warning in w:
            warnings.warn(
                message=warning.message,
                category=warning.category,
                stacklevel=2,
                source=warning.source,
            )

    def add_linker_series(
        self,
        metabolite_id: str,
        lower_bound: int = 0,
        upper_bound: int = 1000,
        last2first: bool = False,
        reverse: bool = False,
        timeframes: Optional[List[str]] = None,
        sub_models: Optional[List[str]] = None,
    ):
        """
        Method to create linkers across all existing time periods.

        Args:
            metabolite_id: The ID to be used for the metabolite. This should match
                the ID of the metabolite in the model.
            lower_bound: The 'lower_bound' to be used for the reaction.
                For more information see :py:attr:`cobra.Reaction.lower_bound`
                in :py:func:`cobra.Reaction`.
            upper_bound: The 'upper_bound' to be used for the reaction.
                For more information see :py:attr:`lower_bound` in
                :py:class:`cobra.Reaction.`.
            last2first: Bool that determines whether a linker should be created
                between the last and the first period.
                If True said linker will be created.
                If reverse equals True, a linker will be created
                from the first to the last period.
            reverse: Bool that specifies the orientation of the linkers.
                If True, the linkers are created starting from the last to the
                first time period and not from the first to the last as usual.
            sub_models:
            timeframes:
        Examples:
            Application to a four phase model:

            >>> con = Constraints()
            >>> con.add_time_slots(4, 1)
            >>> con.add_linker_series("ATP")
            >>> print(con.linker)
            +-----+------+-----------+-------------+--------------+--------------+
            |  ID | Name |   Source  | Destination | Lower Bounds | Upper Bounds |
            +-----+------+-----------+-------------+--------------+--------------+
            | ATP |      | default-0 |  default-1  |      0       |     1000     |
            | ATP |      | default-1 |  default-2  |      0       |     1000     |
            | ATP |      | default-2 |  default-3  |      0       |     1000     |
            +-----+------+-----------+-------------+--------------+--------------+
        """  # noqa: E501

        labels, times = self.__get_label_time(reverse=reverse)

        if sub_models is not None:
            labels = [label for label in labels if label in sub_models]

        if timeframes is not None:
            times = [time for time in times if time in timeframes]

        for label in labels:
            for n in range(len(times) - 1):
                time = times[n]
                # try:
                linker = Linker(
                    metabolite_id=metabolite_id,
                    source=f"{label}-{time}",
                    destination=f"{label}-{times[n + 1]}",
                    upper_bound=upper_bound,
                    lower_bound=lower_bound,
                )
                with warnings.catch_warnings(record=True) as w:
                    self.add_linker(linker)
                for warning in w:
                    warnings.warn(
                        message=warning.message,
                        category=warning.category,
                        stacklevel=2,
                        source=warning.source,
                    )

            if last2first:
                linker = Linker(
                    metabolite_id=metabolite_id,
                    source=f"{label}-{times[-1]}",
                    destination=f"{label}-{times[0]}",
                    upper_bound=upper_bound,
                    lower_bound=lower_bound,
                )
                with warnings.catch_warnings(record=True) as w:
                    self.add_linker(linker)
                for warning in w:
                    warnings.warn(
                        message=warning.message,
                        category=warning.category,
                        stacklevel=2,
                        source=warning.source,
                    )

    def add_transfer_series(
        self,
        metabolite_id: str,
        lower_bound: int = 0,
        upper_bound: int = 1000,
        last2first: bool = False,
        reverse: bool = False,
        timeframes: Optional[List[str]] = None,
        sub_models: Optional[List[str]] = None,
    ):
        """
        Method to create linkers across all existing time periods.

        Args:
            metabolite_id: The ID to be used for the metabolite. This should match
                the ID of the metabolite in the model.
            lower_bound: The 'lower_bound' to be used for the reaction.
                For more information see :py:attr:`cobra.Reaction.lower_bound`
                in :py:func:`cobra.Reaction`.
            upper_bound: The 'upper_bound' to be used for the reaction.
                For more information see :py:attr:`lower_bound` in
                :py:class:`cobra.Reaction.`.
            last2first: Bool that determines whether a linker should be created
                between the last and the first period.
                If True said linker will be created.
                If reverse equals True, a linker will be created
                from the first to the last period.
            reverse: Bool that specifies the orientation of the linkers.
                If True, the linkers are created starting from the last to the
                first time period and not from the first to the last as usual.
            sub_models:
            timeframes:
        Examples:
            Application to a four phase model:

            >>> con = Constraints()
            >>> con.add_time_slots(4, 1)
            >>> con.add_transfer_series("ATP")
            >>> print(con.transfers)
            +-----+------+-----------+-------------+--------------+--------------+
            |  ID | Name |   Source  | Destination | Lower Bounds | Upper Bounds |
            +-----+------+-----------+-------------+--------------+--------------+
            | ATP |      | default-0 |  default-1  |      0       |     1000     |
            | ATP |      | default-1 |  default-2  |      0       |     1000     |
            | ATP |      | default-2 |  default-3  |      0       |     1000     |
            +-----+------+-----------+-------------+--------------+--------------+
        """  # noqa: E501

        labels, times = self.__get_label_time(reverse=reverse)

        if sub_models is not None:
            labels = [label for label in labels if label in sub_models]

        if timeframes is not None:
            times = [time for time in times if time in timeframes]

        for label in labels:
            for n in range(len(times) - 1):
                time = times[n]
                # try:
                transfer = Transfer(
                    metabolite_id=metabolite_id,
                    source=f"{label}-{time}",
                    destination=f"{label}-{times[n + 1]}",
                    upper_bound=upper_bound,
                    lower_bound=lower_bound,
                )
                with warnings.catch_warnings(record=True) as w:
                    self.add_transfer(transfer)
                for warning in w:
                    warnings.warn(
                        message=warning.message,
                        category=warning.category,
                        stacklevel=2,
                        source=warning.source,
                    )

            if last2first:
                transfer = Transfer(
                    metabolite_id=metabolite_id,
                    source=f"{label}-{times[-1]}",
                    destination=f"{label}-{times[0]}",
                    upper_bound=upper_bound,
                    lower_bound=lower_bound,
                )
                with warnings.catch_warnings(record=True) as w:
                    self.add_transfer(transfer)
                for warning in w:
                    warnings.warn(
                        message=warning.message,
                        category=warning.category,
                        stacklevel=2,
                        source=warning.source,
                    )

    def apply_to_model(self, model: Optional[Model] = None) -> Model:
        """
        Method to apply all defined adjustments to a :py:class:`Model`.

        Args:
            model: The model that should be changed.

        Returns: A :py:class:`Model` that contains all defined adjustments.

        """

        new_model = self.phases.apply_phases(model)
        # TODO: verify if transfers should be apply before linker
        new_model = self.transfers.apply(new_model, phases=self.phases)
        new_model = self.linker.apply(new_model, phases=self.phases)

        return new_model

    def to_xml(self) -> Element:
        """
        Converts a :py:class:`Constraints` object to an :py:class:`Element`.

        Returns:
            An :py:class:`Element` that represents a :py:class:`Constraints`
            object.

        """
        root = Element("Conf")
        root.set(
            "xmlns",
            "https://github.com/Toepfer-Lab/"
            "cobra2d/blob/main/src/resources/schema.xsd",
        )

        root.append(self.phases.to_xml())
        root.append(self.transfers.to_xml())
        root.append(self.linker.to_xml())

        return root

    def save_as_xml(self, path: Union[Path, str]):
        """
        Method to save the constraints object as XML file. Based on this file
        the constraints object can be reconstructed.

        Args:
            path: The file path where the created XML file should be saved.

        """

        if isinstance(path, str):
            path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = self.to_xml()

        xml_string = minidom.parseString(
            ElementTree.tostring(data)
        ).toprettyxml(indent="    ")

        with open(path, "w") as file:
            file.write(xml_string)

    @classmethod
    def load_from_xml(cls, path: Union[Path, str, TextIO]) -> Constraints:
        """
        Method to create a :py:class:`Constraints` object from an XML file.
        This must match the format of the XSD found at
        https://github.com/Toepfer-Lab/model_duplication/blob/main/src/recources/schema.xsd.

        Args:
            path: The path to the XML file to be used for creating a
                :py:class:`Constraints` object.

        Returns:
            The :py:class:`Constraints` object created on the properties in the
            XML file.

        """  # nopep8

        if isclass(cls):
            constraints = cls()
        else:
            assert isinstance(cls, Phases)
            constraints = cls

        if isinstance(path, str):
            path = Path(path)

        with open_text(resources, "schema.xsd", encoding="UTF-8") as file:
            xsd = XMLSchema(file)

        # 'to_etree' returns only root. Therefore the same logic as for
        # encoding cannot be used.
        data: Any = xsd.to_dict(path, attr_prefix="")

        print(data)
        constraints.phases = Phases.from_dict(data["phases"]["phase"])
        constraints.transfers = Transfers.from_dict(
            data["Transfers"]["transfer"]
        )
        constraints.linker = Linkage.from_dict(data["linkage"]["linker"])

        if (
            len(constraints.phases.phases) == 1
            and constraints.phases.phases[0].id == "default-0"
        ):
            return constraints

        labels: list = []
        times: list = []

        for phase in constraints.phases.phases:
            label, time = phase.id.split("-", maxsplit=1)
            labels.append(label)
            times.append(time)

        labels = list(OrderedDict.fromkeys(labels))
        times = list(OrderedDict.fromkeys(times))

        # NOTE The following two loops reconstruct time_ranges and sub_models
        # only insufficiently.Only one phase is used to determine which
        # parameters were originally used. However,these could differ from
        # the actual ones. The parameters could potentially also be stored
        # in the XML. However, this would have the consequence that
        # this would be more difficult for a human being to work on.

        if len(labels) == 1 and labels[0] == "default-0":
            pass
        else:
            constraints.default_sub_model = False
            constraints.sub_models.clear()

            for label in labels:
                example_phase = constraints.phases.phases.get_by_id(
                    f"{label}-{times[0]}"
                )
                constraints.sub_models.append(
                    (
                        label,
                        example_phase.volume,
                        example_phase.name.split("-")[0],
                    )
                )

        if len(times) == 1 and times[0] == "1":
            pass
        else:
            constraints.default_time = False
            constraints.time_ranges.clear()

            for time in times:
                example_phase = constraints.phases.phases.get_by_id(
                    f"{labels[0]}-{time}"
                )
                constraints.time_ranges.append(
                    (
                        int(time),
                        example_phase.timeframe,
                        example_phase.light_dark,
                    )
                )

        constraints.index_time_ranges = max([int(x) for x in times])

        return constraints

    def create_graph(self) -> Digraph:
        g = Digraph(engine="dot")
        labels, times = self.__get_label_time()
        invis_connections: List[Tuple[str, str]] = []

        for label in labels:
            with g.subgraph(name=f"cluster_{label}") as sub:
                sub.attr(label=label)
                last_label = None
                for time in times:
                    new_label = f"{label}-{time}"
                    if self.phases.phases.has_id(new_label):
                        sub.node(f"{label}-{time}")

                        if last_label is not None:
                            connection = (last_label, new_label)
                            invis_connections.append(connection)

                        last_label = new_label

        linker_edge_dict: Dict[str, List[Tuple[str, str]]] = {}
        linker_edge_dict_reverse: Dict[Tuple[str, str], list[str]] = {}
        transfer_edge_dict: Dict[str, List[Tuple[str, str]]] = {}
        transfer_edge_dict_reverse: Dict[Tuple[str, str], list[str]] = {}

        for linker in self.linker.linker:
            edge_value: Tuple[str, str] = (linker.source, linker.destination)
            if linker.metabolite_id in linker_edge_dict:
                linker_edge_dict[linker.metabolite_id].append(edge_value)
            else:
                linker_edge_dict[linker.metabolite_id] = [edge_value]

            if edge_value in linker_edge_dict_reverse:
                linker_edge_dict_reverse[edge_value].append(
                    linker.metabolite_id
                )
            else:
                linker_edge_dict_reverse[edge_value] = [linker.metabolite_id]

        for transfer in self.transfers.transfers:
            edge_value: Tuple[str, str] = (  # type: ignore
                transfer.source,
                transfer.destination,
            )
            if transfer.metabolite_id in transfer_edge_dict:
                transfer_edge_dict[transfer.metabolite_id].append(edge_value)
            else:
                transfer_edge_dict[transfer.metabolite_id] = [edge_value]

            if edge_value in transfer_edge_dict_reverse:
                transfer_edge_dict_reverse[edge_value].append(
                    transfer.metabolite_id
                )
            else:
                transfer_edge_dict_reverse[edge_value] = [
                    transfer.metabolite_id
                ]

        size = len(linker_edge_dict_reverse)
        linker_str = "linker existing in all connections:"
        for key, value in linker_edge_dict.items():
            if len(value) == size:
                linker_str += f"\n {key}"
                for metabolite_ids in linker_edge_dict_reverse.values():
                    metabolite_ids.remove(key)

        size = len(transfer_edge_dict_reverse)
        transfer_str = "Transfers existing in all connections:"
        for key, value in transfer_edge_dict.items():
            if len(value) == size:
                transfer_str += f"\n {key}"
                for metabolite_ids in transfer_edge_dict_reverse.values():
                    metabolite_ids.remove(key)

        for key_r, value_r in linker_edge_dict_reverse.items():
            source, destintaion = key_r
            g.edge(
                source,
                destintaion,
                label="\t\n".join(value_r),
                labeldistance="6",
                labelangle="75",
            )

        for key_r, value_r in transfer_edge_dict_reverse.items():
            source, destintaion = key_r
            g.edge(
                source,
                destintaion,
                label="\t\n".join(value_r),
                labeldistance="6",
                labelangle="75",
            )

        for source, destintaion in invis_connections:
            if (source, destintaion) not in linker_edge_dict_reverse.keys():
                g.edge(
                    source,
                    destintaion,
                    style="invis",
                    dir="none",
                )

        g.node(linker_str, shape="rectangle")

        # g.attr(size='6,6')
        return g

    def _constraint2networkx(self):
        graph = nx.DiGraph()

        for phase in self.phases.phases:
            graph.add_node(
                phase.id,
                Timeframe=phase.timeframe,
                Volume=phase.volume,
                Model=getattr(phase, "model", "None"),
                Number_of_Reactions=len(phase.reaction_settings),
            )

        for linker in self.linker.linker:
            graph.add_edge(
                linker.source,
                linker.destination,
                label=linker.metabolite_id,
            )

        for transfer in self.transfers.transfers:
            graph.add_edge(
                transfer.source,
                transfer.destination,
                label=transfer.metabolite_id,
            )

        linker_edge_dict_reverse = {}
        transfer_edge_dict_reverse = {}

        for linker in self.linker.linker:
            value: Tuple[str, str] = (linker.source, linker.destination)

            if value in linker_edge_dict_reverse:
                linker_edge_dict_reverse[value].append(linker.metabolite_id)
            else:
                linker_edge_dict_reverse[value] = [linker.metabolite_id]

        for transfer in self.transfers.transfers:
            value: Tuple[str, str] = (transfer.source, transfer.destination)

            if value in transfer_edge_dict_reverse:
                transfer_edge_dict_reverse[value].append(
                    transfer.metabolite_id
                )
            else:
                transfer_edge_dict_reverse[value] = [transfer.metabolite_id]

        for key, value in linker_edge_dict_reverse.items():
            source, destintaion = key
            graph.add_edge(source, destintaion, Metabolite="\n".join(value))

        for key, value in transfer_edge_dict_reverse.items():
            source, destintaion = key
            graph.add_edge(source, destintaion, Metabolite="\n".join(value))

        return graph

    def _con2json(self):
        nodes = []
        edges = []
        sub_models, times = self.__get_label_time()

        for sub_model in sub_models:
            nodes.append({"data": {"id": sub_model, "type": "sub_model"}})

        for phase in self.phases.phases:
            sub_model, time = phase.id.split("-", maxsplit=1)
            model = getattr(phase, "model", None)
            model_name: str

            if model is None:
                model_name = "Undefined"
            else:
                model_name = model.id

            nodes.append(
                {
                    "data": {
                        "type": "phase",
                        "time": time,
                        "parent": sub_model,
                        "id": phase.id,
                        "Volume": phase.volume,
                        "Timeframe": phase.timeframe,
                        "Number of Reactions": phase.reaction_settings,
                        "Model Name": model_name,
                    }
                }
            )

        linker_edge_dict = {}
        linker_edge_dict_reverse = {}
        transfer_edge_dict = {}
        transfer_edge_dict_reverse = {}

        for linker in self.linker.linker:
            value: Tuple[str, str] = (linker.source, linker.destination)
            if linker.metabolite_id in linker_edge_dict:
                linker_edge_dict[linker.metabolite_id].append(value)
            else:
                linker_edge_dict[linker.metabolite_id] = [value]

            if value in linker_edge_dict_reverse:
                linker_edge_dict_reverse[value].append(linker.metabolite_id)
            else:
                linker_edge_dict_reverse[value] = [linker.metabolite_id]

        for transfer in self.transfers.transfers:
            value: Tuple[str, str] = (linker.source, linker.destination)
            if transfer.metabolite_id in transfer_edge_dict:
                transfer_edge_dict[transfer.metabolite_id].append(value)
            else:
                transfer_edge_dict[transfer.metabolite_id] = [value]

            if value in transfer_edge_dict_reverse:
                transfer_edge_dict_reverse[value].append(
                    transfer.metabolite_id
                )
            else:
                transfer_edge_dict_reverse[value] = [transfer.metabolite_id]

        size = len(linker_edge_dict_reverse)
        metabolites_existing_between_all_phases_linker = []
        metabolites_existing_between_all_phases_transfer = []

        for key, value in linker_edge_dict.items():
            if len(value) == size:
                metabolites_existing_between_all_phases_linker.append(key)
                for metabolite_ids in linker_edge_dict_reverse.values():
                    metabolite_ids.remove(key)

        for key, value in linker_edge_dict_reverse.items():
            source, destination = key
            edges.append(
                {
                    "data": {
                        "id": f"Linker from {source} to {destination}",
                        "source": source,
                        "target": destination,
                        "Metabolite": value,
                        "isdirected": "true",
                    }
                }
            )

        size = len(transfer_edge_dict_reverse)
        for key, value in transfer_edge_dict.items():
            if len(value) == size:
                metabolites_existing_between_all_phases_transfer.append(key)
                for metabolite_ids in transfer_edge_dict_reverse.values():
                    metabolite_ids.remove(key)

        for key, value in transfer_edge_dict_reverse.items():
            source, destination = key
            edges.append(
                {
                    "data": {
                        "id": f"Transfer from {source} to {destination}",
                        "source": source,
                        "target": destination,
                        "Metabolite": value,
                        "isdirected": "true",
                    }
                }
            )

        return (
            {"nodes": nodes, "edges": edges},
            metabolites_existing_between_all_phases_linker,
            metabolites_existing_between_all_phases_transfer,
        )

    def cytoscape(self):  # pragma: no cover
        # is covered in ui-tests
        tab = "&nbsp;&nbsp;&nbsp;&nbsp;"

        cytoscapeobj = ipycytoscape.CytoscapeWidget()
        (
            graph,
            met_betw_all_phases_linker,
            met_betw_all_phases_transfer,
        ) = self._con2json()
        cytoscapeobj.graph.add_graph_from_json(graph, directed=True)
        cytoscapeobj.set_layout(name="dagre", nodeSpacing=50, edgeLengthVal=10)

        cytoscapeobj.set_style(
            [
                {
                    "selector": 'node[type="phase"]',
                    "css": {
                        "content": "data(id)",
                        "text-valign": "center",
                        "text-halign": "left",
                        "color": "black",
                        "background-color": "#11479e",
                        "text-wrap": "none",
                    },
                },
                {
                    "selector": "edge",
                    "style": {
                        "line-color": "#9dbaea",
                        "curve-style": "haystack",
                        "text-wrap": "wrap",
                    },
                },
                {
                    "selector": "edge.directed",
                    "style": {
                        "curve-style": "bezier",
                        "target-arrow-shape": "triangle",
                        "target-arrow-color": "#9dbaea",
                    },
                },
                {
                    "selector": 'node[type="legend"]',
                    "style": {
                        "shape": "square",
                        "background-color": "red",
                        "text-valign": "center",
                        "content": "data(text)",
                        "text-wrap": "wrap",
                    },
                },
                {
                    "selector": ":selected",
                    "css": {
                        "background-color": "black",
                        "line-color": "black",
                        "target-arrow-color": "black",
                        "source-arrow-color": "black",
                        "text-outline-color": "black",
                    },
                },
                {
                    "selector": ":parent",
                    "css": {
                        "content": "data(id)",
                        "text-valign": "top",
                        "text-halign": "center",
                        "background-opacity": 0.333,
                    },
                },
            ]
        )

        out = Output()
        all_met_betw_all_phases_linker = iter(met_betw_all_phases_linker)
        all_met_betw_all_phases_transfer = iter(met_betw_all_phases_transfer)

        try:
            met_betw_all_phases_linker_html = (
                f"{tab}&bull; {next(all_met_betw_all_phases_linker)}<br>"
            )
            if len(met_betw_all_phases_linker) > 1:
                met_betw_all_phases_linker_html += f"{tab}&bull; "
        except StopIteration:
            met_betw_all_phases_linker_html = f"{tab}None"

        met_betw_all_phases_linker_html += (f"<br>{tab}&bull; ").join(
            all_met_betw_all_phases_linker
        )

        try:
            met_betw_all_phases_transfer_html = (
                f"{tab}&bull; {next(all_met_betw_all_phases_transfer)}<br>"
            )
            if len(met_betw_all_phases_transfer) > 1:
                met_betw_all_phases_transfer_html += f"{tab}&bull; "
        except StopIteration:
            met_betw_all_phases_transfer_html = f"{tab}None"

        met_betw_all_phases_transfer_html += (f"<br>{tab}&bull; ").join(
            all_met_betw_all_phases_transfer
        )

        met_betw_all_phases_linker_html = (
            "<h5>Linker existing between all Phases:</h5>"
            + met_betw_all_phases_linker_html
        )
        met_betw_all_phases_transfer_html = (
            "<h5>Transfers existing between all Phases:</h5>"
            + met_betw_all_phases_transfer_html
        )

        def log_mouseovers_edge(edge):
            with out:
                out.clear_output(wait=True)
                id = edge["data"]["id"]
                all_metabolites = edge["data"]["Metabolite"]
                metabolites = iter(all_metabolites)

                try:
                    metabolites_html = f"{tab}&bull; {next(metabolites)}"
                except StopIteration:
                    metabolites_html = f"{tab}None"

                metabolites_html += (f"<br>{tab}&bull; ").join(metabolites)

                display(
                    HTML(
                        f"<h4>{id}</h4>"
                        f"{met_betw_all_phases_linker_html}<br>"
                        f"{met_betw_all_phases_transfer_html}<br>"
                        f"<h5>Additional metabolites:</h5>"
                        f"{metabolites_html}"
                    )
                )

        model2viz = {}

        def log_mouseovers_node(node):
            with out:
                try:
                    #  If sub_model does not exist, it's a parent node
                    #  where we don't want to show anything
                    sub_model = node["data"]["parent"]
                except KeyError:
                    return
                phase_id = node["data"]["id"]
                phase = self.get_phase_by_id(phase_id)

                time = node["data"]["time"]
                model_name = node["data"]["Model Name"]

                all_reactions = iter(phase.reaction_settings)
                try:
                    reactions_html_str = (
                        f"{tab}&bull; {next(all_reactions).id}<br>"
                    )
                except StopIteration:
                    reactions_html_str = f"{tab}None"

                reactions_html_str += "&nbsp;" * 16 + (
                    "<br>" + "&nbsp;" * 16
                ).join(reaction.id for reaction in all_reactions)

                out.clear_output(wait=True)

                phase_description = HTML(
                    f"<h4>Phase id: {phase_id}</h4>"
                    f"<h5>Phase affiliation:</h5>"
                    f"{tab}&bull; Time: {time}<br>"
                    f"{tab}&bull; SubModel: {sub_model}<br>"
                    f"<h5>Phase settings:</h5>"
                    f"{tab}&bull; Name: {phase.name}<br>"
                    f"{tab}&bull; Volume: {phase.volume}<br>"
                    f"{tab}&bull; Timeframe: {phase.timeframe}<br>"
                    f"{tab}&bull; Model: {model_name}<br>"
                    f"{tab}&bull; Reactions: {reactions_html_str}"
                )
                if phase.model is not None:
                    try:
                        viz_selection = model2viz[phase.model]
                    except KeyError:
                        viz_selection = metexplore_interface(phase.model)
                        model2viz[phase.model] = viz_selection

                    box = Tab()
                    box.children = [phase_description, viz_selection]
                    box.set_title(0, "Phase")
                    box.set_title(1, "Visualization")

                    # box.layout = Layout(
                    #     display="flex",
                    #     justify_content="space-between"
                    # )
                else:
                    box = Tab()
                    box.children = [phase_description]
                    box.set_title(0, "Phase")
                display(box)

        cytoscapeobj.on("edge", "click", log_mouseovers_edge)
        cytoscapeobj.on("node", "click", log_mouseovers_node)

        display(cytoscapeobj)
        display(out)
        for phase in self.phases.phases:
            if phase.model is not None:
                model2viz[phase.model] = metexplore_interface(phase.model)
