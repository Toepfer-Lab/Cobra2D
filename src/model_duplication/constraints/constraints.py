from __future__ import annotations

from collections import OrderedDict
from importlib.resources import open_text
from inspect import isclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Tuple, Union
from xml.dom import minidom
from xml.etree import ElementTree

from typing_extensions import Literal
from xml.etree.ElementTree import Element

from cobra import Model, Reaction
from prettytable import PrettyTable
from rich.console import Console
from rich.table import Table
from xmlschema import XMLSchema

import recources
from model_duplication.constraints.linker import Linkage, Linker
from model_duplication.constraints.phase import Phase, Phases
from model_duplication.error import InvalidLabel
from model_duplication.utils import Matrix


class Constraints:
    phases: Phases
    order: Matrix
    linker: Linkage

    default_time = True
    default_sub_model = True

    time_ranges: List[Tuple[int, int, Literal["light", "dark"]]] = [
        (0, 1, "light")
    ]

    index_time_ranges = 0

    sub_models: List[Tuple[str, int, str]] = [
        ("default", 1, "Default sub_model")
    ]

    def __init__(self):
        self.phases = Phases()
        self.linker = Linkage()
        self.order = Matrix()
        self.phases.add_phase(
            Phase(id="default", name="Default Phase", light_dark="light")
        )

    def __str__(self):
        output = PrettyTable(
            ["Sub-Model\\Time Index"]
            + list(str(time[0]) for time in self.time_ranges)
        )
        for label, volume, name in self.sub_models:
            row = [
                " " * (len(label) - 1) + "| id\n"
                f"{label}  | volume\n" + (" " * len(label)) + "| time"
            ]

            for index, timeframe, light in self.time_ranges:
                row.append(f"{label}-{index}\n" f"{volume}\n" f"{timeframe}")

            output.add_row(row)
            output.hrules = 1

        return output.get_string()

    def get_phase_by_id(self, id: str) -> Phase:
        return self.phases.phases.get_by_id(id)

    def add_reaction_to_phase(
        self,
        reaction: Reaction,
        phase: Union[Union[str, Phase], List[str], List[Phase]],
    ):

        if isinstance(phase, List):
            for single_phase in phase:
                self.add_reaction_to_phase(reaction, single_phase)
                return

        if isinstance(phase, str):
            phase = self.phases.phases.get_by_id(phase)

        assert isinstance(phase, Phase)
        phase.add_reaction(reaction)

    def rich_output(self):
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

    def add_linker(self, linker: Linker):
        # ToDo check if phase ID/Phase exist for reference

        self.linker.add_linker(linker)

    def apply_to_model(self, model: Model):

        new_model = self.phases.apply_phases(model)
        new_model = self.linker.apply_linkage(new_model, phases=self.phases)

        return new_model

    def to_xml(self) -> Element:
        root = Element("Conf")
        root.set(
            "xmlns",
            "https://github.com/Toepfer-Lab/"
            "model_duplication/blob/main/src/recources/schema.xsd",
        )

        root.append(self.phases.to_xml())
        root.append(self.linker.to_xml())

        return root

    def save_as_xml(self, path: Union[Path, str]):

        if isinstance(path, str):
            path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = self.to_xml()

        data = minidom.parseString(ElementTree.tostring(data)).toprettyxml(
                indent="    "
        )

        with open(path, "w") as file:
            file.write(data)

    @classmethod
    def load_from_xml(cls, path: Union[Path, str]) -> Constraints:

        if isclass(cls):
            constraints = cls()
        else:
            assert isinstance(cls, Phases)
            constraints = cls

        if isinstance(path, str):
            path = Path(path)

        xsd = XMLSchema(open_text(recources, "schema.xsd", encoding="UTF-8"))

        # 'to_etree' returns only root. Therefore the same logic as for
        # encoding cannot be used.
        data: Any = xsd.to_dict(path, attr_prefix="")

        constraints.phases = Phases.from_dict(data["phases"]["phase"])
        constraints.linker = Linkage.from_dict(data["linkage"]["linker"])

        if (
            len(constraints.phases.phases) == 1
            and constraints.phases.phases[0].id == "default"
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

        if len(labels) == 1 and labels[0] == "default":
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
                    (time, example_phase.timeframe, example_phase.light_dark)
                )

        constraints.index_time_ranges = max([int(x) for x in times])

        return constraints
