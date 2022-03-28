from __future__ import annotations

import logging
from inspect import isclass
from typing import List, Union
from xml.etree.ElementTree import Element, SubElement

from cobra import Metabolite, Model, Reaction
from prettytable import PrettyTable

from model_duplication.constraints.phase import Phase, Phases


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.level = 20


class Linker(Metabolite):
    source: Union[Phase, str]
    destination: Union[Phase, str]
    lower_bound: int
    upper_bound: int

    def __init__(
        self,
        id: str,
        source: Union[Phase, str],
        destination: Union[Phase, str],
        lower_bound: int = 0,
        upper_bound: int = 1000,
        *args,
        **kwargs
    ):
        super().__init__(id=id, *args, **kwargs)

        if isinstance(source, Phase):
            source = source.id

        if isinstance(destination, Phase):
            destination = destination.id

        self.source = source
        self.destination = destination
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __str__(self):
        output = PrettyTable(
            [
                "ID",
                "Name",
                "Source",
                "Destination",
                "Lower Bounds",
                "Upper Bounds",
            ]
        )

        return output.get_string()

    def to_xml(self) -> Element:
        element = Element("linker")
        SubElement(element, "destination").set("refid", self.destination)
        SubElement(element, "source").set("refid", self.source)

        element.set("id", self.id)
        element.set("lower_bound", str(self.lower_bound))
        element.set("upper_bound", str(self.upper_bound))

        return element

    @classmethod
    def from_dict(cls, data: dict) -> Linker:
        return cls(
            id=data["id"],
            lower_bound=int(data["lower_bound"]),
            upper_bound=int(data["upper_bound"]),
            destination=data["destination"]["refid"],
            source=data["source"]["refid"],
        )


class Linkage:
    # ToDo change to Set? or to DictList
    linker: List[Linker]

    def __init__(self):
        self.linker = []

    def __str__(self):
        output = PrettyTable(
            [
                "ID",
                "Name",
                "Source",
                "Destination",
                "Lower Bounds",
                "Upper Bounds",
            ]
        )
        for linker in self.linker:
            output.add_row(
                [
                    linker.id,
                    linker.name,
                    linker.source,
                    linker.destination,
                    linker.lower_bound,
                    linker.upper_bound,
                ]
            )
        return output.get_string()

    def add_linker(self, linker: Linker):
        # ToDo check for duplicates?
        self.linker.append(linker)

    def remove_linker(self, obj_pos: Union[Linker, int]):
        if isinstance(obj_pos, int):
            del self.linker[obj_pos]
            return

        self.linker.remove(obj_pos)

    def apply_linkage(self, model: Model, phases: Phases):
        reactions2add: List[Reaction] = []

        for link in self.linker:
            source = phases.phases.get_by_id(link.source)
            destination = phases.phases.get_by_id(link.destination)

            source_metabolite: Metabolite = model.metabolites.get_by_id(
                link.id + "_" + link.source
            )
            destination_metabolite: Metabolite = model.metabolites.get_by_id(
                link.id + "_" + link.destination
            )

            linker: Reaction = Reaction(
                id=link.id + "_L_" + link.source + "_" + link.destination,
                name="Linker for "
                + link.id
                + " from "
                + link.source
                + " to "
                + link.destination,
                subsystem="Linker",
                lower_bound=link.lower_bound,
                upper_bound=link.upper_bound,
            )

            linker.add_metabolites(
                {
                    source_metabolite: -destination.volume
                    * destination.timeframe,
                    destination_metabolite: source.volume * source.timeframe,
                }
            )

            reactions2add.append(linker)

        model.add_reactions(reactions2add)

        return model

    def to_xml(self) -> Element:

        root = Element("linkage")
        for linker in self.linker:
            root.append(linker.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: dict) -> Linkage:
        if isclass(cls):
            linkage = cls()
        else:
            assert isinstance(cls, Linkage)
            linkage = cls

        for linker_dict in data:
            new_linker = Linker.from_dict(linker_dict)
            linkage.add_linker(new_linker)

        return linkage
