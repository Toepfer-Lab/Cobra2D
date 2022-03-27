from __future__ import annotations

from inspect import isclass
from typing import Literal, List, Union
from xml.etree.ElementTree import Element

from cobra import Reaction, Model, DictList
from prettytable import PrettyTable

from model_duplication.duplication.duplication import _main_placeholder
from model_duplication.error import IdAlreadyInUse


class Phase:
    id: str
    name: str

    # ToDo light_dark maybe add None if not using
    light_dark: Literal["light", "dark"]
    timeframe: int
    volume: int
    reaction_settings: List[Reaction]

    def __init__(
        self,
        id: str,
        light_dark: Literal["light", "dark"],
        timeframe: int = 1,
        volume: int = 1,
        name: str = "",
    ):
        self.id = id
        self.volume = volume
        self.name = name
        self.light_dark = light_dark
        self.timeframe = timeframe

    def to_xml(self):
        element = Element("phase")

        element.set("id", self.id)
        element.set("volume", str(self.volume))
        element.set("name", (self.name))
        element.set("light_dark", self.light_dark)
        element.set("timeframe", str(self.timeframe))

        return element

    @classmethod
    def from_dict(cls, data: dict) -> Phase:
        return cls(
            id=data["id"],
            volume=int(data["volume"]),
            name=data["name"],
            light_dark=data["light_dark"],
            timeframe=int(data["timeframe"]),
        )


class Phases:
    phases: DictList[Phase]

    def __init__(self):
        self.phases = DictList()

    def __str__(self):
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        for phase in self.phases:
            output.add_row(
                [phase.id, phase.name, phase.volume, phase.timeframe]
            )

        return output.get_string()

    def clear_phases(self):
        del self.phases
        self.phases = DictList()

    def add_phase(self, phase: Phase):

        if self.phases.has_id(phase.id):
            raise IdAlreadyInUse(phase.id)

        self.phases.append(phase)

    def remove_phase(self, phase: Union[Phase, str]):
        id: str = phase.id if isinstance(phase, Phase) else phase

        if not self.phases.has_id(id):
            raise KeyError(f" There is no phase with ID: {id}")

        del self.phases[self.phases.index(id)]

    def apply_phases(self, model: Model, link_genes: bool = False):
        phase_names = [phase.id for phase in self.phases]

        new_model = _main_placeholder(
            model=model, labels=phase_names, file=None, genes=link_genes
        )

        # ToDo change specified Reactions

        return new_model

    def to_xml(self) -> Element:

        root = Element("phases")

        for phase in self.phases:
            root.append(phase.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: dict) -> Phases:
        if isclass(cls):
            phases = cls()

        else:
            assert isinstance(cls, Phases)
            phases = cls

        for phase_dict in data:
            new_phase = Phase.from_dict(phase_dict)
            phases.add_phase(new_phase)

        return phases
