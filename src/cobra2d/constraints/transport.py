"""
Implementation of the abstract class for the transport of a metabolite between
phases. The transport is later represented in the model by pseudo reactions.
The properties of these reactions are also defined here.
"""

from __future__ import annotations

import logging
import warnings
from abc import ABC, abstractmethod
from typing import Union, List
from xml.etree.ElementTree import Element

from cobra import Model, Metabolite, Reaction
from prettytable import PrettyTable

from cobra2d.constraints.phase import Phase, Phases


def split_phase_id(phase_id: str) -> tuple[str, str]:
    """Split a phase ID into its sub_model and time components.

    Phase IDs follow the ``<sub_model>_<time>`` pattern (e.g. ``leaf_1``).
    The sub_model may itself contain underscores (e.g. ``leaf_2_1`` is the
    sub_model ``leaf_2`` at time ``1``), so the split is done on the *last*
    underscore. The time period must therefore not contain an underscore.

    Args:
        phase_id: The ID of the phase to split.

    Returns:
        A ``(sub_model, time)`` tuple.

    Raises:
        ValueError: If the ID does not contain a ``_`` separating the
            sub_model from the time.
    """
    sub_model, sep, time = phase_id.rpartition("_")
    if not sep:
        raise ValueError(
            f"Phase ID '{phase_id}' cannot be split into "
            f"'<sub_model>_<time>'. Expected a '_' separating the sub_model "
            f"from the time period."
        )
    return sub_model, time


class Transport(ABC):
    """ """

    metabolite_id: str
    source: str
    destination: str
    lower_bound: float
    upper_bound: float

    @abstractmethod
    def __init__(
        self,
        metabolite_id: str,
        source: Union[Phase, str],
        destination: Union[Phase, str],
        lower_bound: float = 0.0,
        upper_bound: float = 1000.0,
    ):
        if isinstance(source, Phase):
            source = source.id

        if isinstance(destination, Phase):
            destination = destination.id

        self.metabolite_id = metabolite_id
        self.source = source
        self.destination = destination
        # Bounds are floats throughout, as COBRApy declares them. Converting
        # here keeps a transport that was given whole bounds indistinguishable
        # from the same transport read back from XML.
        self.lower_bound = float(lower_bound)
        self.upper_bound = float(upper_bound)

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

    @property
    @abstractmethod
    def reac_id(self) -> str: ...

    @property
    @abstractmethod
    def reac_name(self) -> str: ...

    @abstractmethod
    def to_xml(self) -> Element: ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> Transport: ...


class Transports(ABC):
    transports: List[Transport]

    @abstractmethod
    def __init__(self):
        self.transports = []

    @abstractmethod
    def __str__(self):
        output = PrettyTable(
            [
                "Metabolite ID",
                "Source",
                "Destination",
                "Lower Bounds",
                "Upper Bounds",
            ]
        )

        item: Transport
        for item in self:
            output.add_row(
                [
                    item.metabolite_id,
                    item.source,
                    item.destination,
                    item.lower_bound,
                    item.upper_bound,
                ]
            )
        return output.get_string()

    @abstractmethod
    def __iter__(self):
        for transport in self.transports:
            yield transport

    @abstractmethod
    def append(self, obj: Transport):
        if isinstance(obj, Transport):
            if obj not in self.transports:
                self.transports.append(obj)
            else:
                warnings.warn(
                    f"{obj.reac_id} is already present. Not added.",
                    stacklevel=3,
                )
        else:
            raise TypeError(
                f" {obj}\n" f"is not of type Transport. Cant add object."
            )

    @abstractmethod
    def remove(self, obj_pos: Union[Transport, int]):
        if isinstance(obj_pos, int):
            del self.transports[obj_pos]

        elif isinstance(obj_pos, Transport):
            self.transports.remove(obj_pos)

        else:
            raise TypeError("An unsupported type was used as input.")

    @abstractmethod
    def apply(self, model: Model, phases: Phases):
        reactions2add: List[Reaction] = []

        for transport in self.transports:
            source: Phase
            destination: Phase

            try:
                source = phases.phases.get_by_id(transport.source)
            except KeyError as e:
                raise KeyError(
                    f"In {transport}, phase {transport.source} was "
                    f"used. However, the phase {transport.source} is"
                    f" unknown to the Phases object."
                ) from e
            try:
                destination = phases.phases.get_by_id(transport.destination)
            except KeyError as e:
                raise KeyError(
                    f"In {transport}, phase {transport.destination} was "
                    f"used. However, the phase {transport.destination} is"
                    f" unknown to the Phases object."
                ) from e

            try:
                source_metabolite: Metabolite = model.metabolites.get_by_id(
                    transport.metabolite_id + "_" + transport.source
                )
            except KeyError as e:
                raise KeyError(
                    f"Metabolite "
                    f"{transport.metabolite_id + '_' + transport.source} was "
                    f"not found in model {model.id}. Associated "
                    f"transport cannot be created. Check that metabolite "
                    f"{transport.metabolite_id} exists in the model associated"
                    f" to phase {transport.source}."
                ) from e
            try:
                destination_metabolite: Metabolite = (
                    model.metabolites.get_by_id(
                        transport.metabolite_id + "_" + transport.destination
                    )
                )
            except KeyError as e:
                raise KeyError(
                    f"Metabolite "
                    f"{transport.metabolite_id + '_' + transport.destination}"
                    f" was not found in model with id {model.id}. Associated "
                    f"transport cannot be created. Check that metabolite "
                    f"{transport.metabolite_id} exists in the model associated"
                    f" to phase {transport.destination}."
                ) from e

            # ToDo set subsystem or not
            reac: Reaction = Reaction(
                id=transport.reac_id,
                name=transport.reac_name,
                lower_bound=transport.lower_bound,
                upper_bound=transport.upper_bound,
            )

            if source_metabolite == destination_metabolite:
                warnings.warn(
                    f"Source and target metabolite are identical. "
                    f"Generation of the reaction is skipped. \n "
                    f"{str(transport)}",
                    category=UserWarning,
                    stacklevel=3,
                )

                continue

            reac.add_metabolites(
                {
                    # source defined as one for visualisation purposes
                    source_metabolite: -1,
                    destination_metabolite: (source.volume * source.timeframe)
                    / (destination.volume * destination.timeframe),
                }
            )
            logging.info(f"The reaction {reac.id} was created")
            reactions2add.append(reac)
            logging.info(
                f"The previously stated reactions (n= {len(reactions2add)}) "
                f"were added to the model."
            )

        model.add_reactions(reactions2add)

        return model

    @abstractmethod
    def to_xml(self) -> Element: ...

    @abstractmethod
    def from_dict(self, data: List[dict]) -> Transports: ...
