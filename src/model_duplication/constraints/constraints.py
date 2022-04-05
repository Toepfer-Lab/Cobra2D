"""
Implementation of the Constraints class.
"""
from __future__ import annotations

import logging
from collections import OrderedDict
from importlib.resources import open_text
from inspect import isclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Tuple, Union, TextIO
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from cobra import Model, Reaction
from prettytable import PrettyTable
from rich.console import Console
from rich.table import Table
from typing_extensions import Literal
from xmlschema import XMLSchema

from model_duplication import resources
from model_duplication.constraints.linker import Linkage, Linker
from model_duplication.constraints.phase import Phase, Phases
from model_duplication.error import InvalidLabel
from model_duplication.utils import Matrix


class Constraints:
    """
    This class bundles the functionalities of :py:class:`Linker` and
    :py:class:`Linkage`. So the application of these is not only possible with
    a single line but there are also helper functions to simplify the creation
    of organs and time periods. Last but not least it realizes a storage of a
    constraints object as XML and also the creation of a constraints object
    based on such an XML file.
    """

    def __init__(self):
        """
        Create a Constraints object.

        """
        self.phases = Phases()
        self.linker = Linkage()
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
    ) -> Tuple[List[str], List[str]]:
        labels: List[str] = []
        times: List[str] = []

        for phase in self.phases.phases:
            label_time = phase.id.split("-")

            labels.append(label_time[0])
            times.append(label_time[1])

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
        return self.phases.phases.get_by_id(id)

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
        self, n_ranges: int, time: int, light_dark: Literal["light", "dark"]
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
        except KeyError:
            raise KeyError(
                f"The destination: '{linker.destination}' is unknown."
            )

        try:
            self.get_phase_by_id(linker.source)
        except KeyError:
            raise KeyError(f"The source: '{linker.source}' is unknown.")

        self.linker.add_linker(linker)

    def add_linker_series(
        self,
        id: str,
        lower_bound: int = 0,
        upper_bound: int = 1000,
        last2first: bool = False,
        reverse: bool = False,
    ):
        """
        Method to create linkers across all existing time periods. As an
        example, the following linkers would be created for a model that
        spans 4 time periods:

        .. code-block::
        Linker from time period 0 to time period 1\n
        Linker from time period 1 to time period 2\n
        Linker from time period 2 to time period 3

        Args:
            id: The ID to be used for the metabolite. This should match
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

        """

        labels, times = self.__get_label_time(reverse=reverse)

        for label in labels:
            for n in range(len(times) - 1):
                time = times[n]
                try:
                    linker = Linker(
                        id=id,
                        source=f"{label}-{time}",
                        destination=f"{label}-{times[n+1]}",
                        upper_bound=upper_bound,
                        lower_bound=lower_bound,
                    )
                    self.add_linker(linker)

                except KeyError:
                    logging.warning(
                        f"Linker from {label}-{time} to "
                        f"{label}-{times[n+1]} could not be "
                        f"created."
                    )

            if last2first:
                linker = Linker(
                    id=id,
                    source=f"{label}-{times[-1]}",
                    destination=f"{label}-{times[0]}",
                    upper_bound=upper_bound,
                    lower_bound=lower_bound,
                )
                self.add_linker(linker)

    def apply_to_model(self, model: Model):
        """
        Method to apply all defined adjustments to a :py:class:`Model`.

        Args:
            model: The model that should be changed.

        Returns: A :py:class:`Model` that contains all defined adjustments.

        """

        new_model = self.phases.apply_phases(model)
        new_model = self.linker.apply_linkage(new_model, phases=self.phases)

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
            "model_duplication/blob/main/src/resources/schema.xsd",
        )

        root.append(self.phases.to_xml())
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

        constraints.phases = Phases.from_dict(data["phases"]["phase"])
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
