"""
Implementation of the abstract class for the transport of a metabolite between
phases. The transport is later represented in the model by pseudo reactions.
The properties of these reactions are also defined here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union, List
from xml.etree.ElementTree import Element

from cobra import Model
from prettytable import PrettyTable

from model_duplication.constraints.phase import Phase, Phases


class Transport(ABC):
    """

    """

    metabolite_id: str
    source: str
    destination: str
    lower_bound: int
    upper_bound: int

    @abstractmethod
    def __init__(
            self,
            metabolite_id: str,
            source: Union[Phase, str],
            destination: Union[Phase, str],
            lower_bound: int = 0,
            upper_bound: int = 1000,
    ):

        if isinstance(source, Phase):
            source = source.id

        if isinstance(destination, Phase):
            destination = destination.id

        self.metabolite_id = metabolite_id
        self.source = source
        self.destination = destination
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @abstractmethod
    def __str__(self) -> str:
        """
        The toString method of the Linker class.
        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of the linker object as a formatted string.

        """
        output = PrettyTable(
            [
                "Metabolite ID",
                "Source",
                "Destination",
                "Lower Bounds",
                "Upper Bounds",
            ]
        )

        output.add_row(
            [
                self.metabolite_id,
                self.source,
                self.destination,
                self.lower_bound,
                self.upper_bound,
            ]
        )

        return output.get_string()

    @abstractmethod
    def __eq__(self, other) -> bool:
        if isinstance(other, Transport):
            if (
                    other.metabolite_id == self.metabolite_id
                    and other.source == self.source
                    and other.destination == self.destination
                    and other.lower_bound == self.lower_bound
                    and other.upper_bound == self.upper_bound
            ):
                return True

        return False

    @abstractmethod
    def to_xml(self) -> Element:
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> Transport:
        ...


class Transports(ABC):

    @abstractmethod
    def __init__(self):
        ...

    @abstractmethod
    def __str__(self):
        ...

    @abstractmethod
    def register(self, obj: Transport):
        ...

    @abstractmethod
    def remove(self, obj_pos: Union[Transport, int]):
        ...

    @abstractmethod
    def apply(self, model: Model, phases: Phases):
        ...

    @abstractmethod
    def to_xml(self) -> Element:
        ...

    @abstractmethod
    def from_dict(self, data: List[dict]) -> Transports:
        ...
