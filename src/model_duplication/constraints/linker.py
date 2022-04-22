"""
Implementation of the Linker and Linkage classes.
"""

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
    """
    Linker is a Subclass of cobra Metabolite. cobra Metabolite is extended with
    information representing the source and target for a metabolite. Source
    and destination represent the same metabolite defined at a fixed time
    period in a fixed organ. Phases are used for this purpose. Using this
    information, a pseudo reaction can be created representing the transition
    between two such phases.

    Attributes:
        source (str): The ID of the source phase.
        destination (str): The ID of the destination phase.
        lower_bound (int): The 'lower_bound' to be used for the reaction.
            For more information see ''lower_bound'' in :func:'cobra.Reaction'.
        upper_bound (int): The 'upper_bound' to be used for the reaction.
            For more information see ''lower_bound'' in :func:'cobra.Reaction'.
    """

    source: str
    destination: str
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
        **kwargs,
    ):
        """
        Initialize a Linker.



        Args:
            id: The ID to be used for the metabolite. This should match
                the ID of the metabolite in the model.
            source: The ID of the source phase or the source
                phase itself.
            destination: The ID of the source phase or the
                source phase itself..
            lower_bound: The 'lower_bound' to be used for the reaction.
                For more information see :py:attr:`cobra.Reaction.lower_bound`
                in :py:func:`cobra.Reaction`.
            upper_bound: The 'upper_bound' to be used for the reaction.
                For more information see :py:attr:`lower_bound` in
                :py:class:`cobra.Reaction.`.
            *args: See :py:class:`cobra.Metabolite` for possible '*args'.
            **kwargs: See :py:class:'cobra.Metabolite' for possible '*kwargs'.
        """
        super().__init__(id=id, *args, **kwargs)

        if isinstance(source, Phase):
            source = source.id

        if isinstance(destination, Phase):
            destination = destination.id

        self.source = source
        self.destination = destination
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __str__(self) -> str:
        """
        The toString method of the Linker class.
        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of the linker object as a formatted string.

        """
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

        output.add_row(
            [
                self.id,
                self.name,
                self.source,
                self.destination,
                self.lower_bound,
                self.upper_bound,
            ]
        )

        return output.get_string()

    def __eq__(self, other) -> bool:
        if isinstance(other, Linker):
            if (
                other.id == self.id
                and other.source == self.source
                and other.destination == self.destination
                and other.lower_bound == self.lower_bound
                and other.upper_bound == self.upper_bound
            ):
                return True

        return False

    def to_xml(self) -> Element:
        """
        Converts a linker to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            a linker.
        """
        element = Element("linker")
        SubElement(element, "destination").set("refid", self.destination)
        SubElement(element, "source").set("refid", self.source)

        element.set("id", self.id)
        element.set("lower_bound", str(self.lower_bound))
        element.set("upper_bound", str(self.upper_bound))

        return element

    @classmethod
    def from_dict(cls, data: dict) -> Linker:
        """
        Creates a linker object based on the data encoded in a dict.

        Args:
            data: A dict that contains the necessary data to create a linker.

        Returns:
            A linker created based on the data from the dict.

        Examples:
            .. code-block:: python

                dictionary = {
                    "id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }
                linker = Linker.from_dict(dictionary)
        """
        return cls(
            id=data["id"],
            lower_bound=int(data["lower_bound"]),
            upper_bound=int(data["upper_bound"]),
            destination=data["destination"]["refid"],
            source=data["source"]["refid"],
        )


class Linkage:
    """
    Linkage as a class represents multiple Linker. Furthermore it implements
    the applying of Linkers to a cobra.model.

    Attributes:
        linker (List[Linker]): A list containing individual Linker.

    """

    # ToDo change to Set? or to DictList
    # COMMENT:So far, the behavior of DictList works flawlessly. This would
    # remove the check for duplicates as long the identifiers are not the same
    linker: List[Linker]

    def __init__(self):
        """
        Initialize a Linkage.
        """
        self.linker = []

    def __str__(self):
        """
        The toString method of the Linkage class.

        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of all linker objects as a formatted string.
        """
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
        """
        Adds linker to the linkage class.

        Args:
            linker: The linker to be added.
        """
        # ToDo check for duplicates?
        self.linker.append(linker)

    def remove_linker(self, obj_pos: Union[Linker, int]):
        """
        Function to remove a linker. Either the position of the linker in the
        :py:attr:`linkage.linker` list can be specified or the respective
        linker.

        Args:
            obj_pos: The position of the linker object to be deleted or it
                itself.

        """
        if isinstance(obj_pos, int):
            del self.linker[obj_pos]
            return

        self.linker.remove(obj_pos)

    def apply_linkage(self, model: Model, phases: Phases) -> Model:
        """
        Function to apply all linkers contained in Linkage to a
        :py:class:`cobra.Model`

        Args:
            model: The model to which the Linker should be applied.
            phases: A phases object that contains all phases referenced by
                the individual Linker.

        Returns:
            A :py:class:`cobra.model` that contains the Linker.
        """
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
                name=f"Linker for {link.id} from {link.source} "
                f"to {link.destination}",
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

        # COMMENT: can exceptions be raised? link.id is None? Or maybe the
        # name of the phase does not exist.
        # Returning a model with not all the reactions might bring wrong
        # results
        return model

    def to_xml(self) -> Element:
        """
        Converts a linkage to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            a linkage.

        """

        root = Element("linkage")
        for linker in self.linker:
            root.append(linker.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Linkage:
        """
        Creates a linkage object based on the data encoded in a dict.

        Args:
            data: A list of dicts that contain the necessary data to create a
                linker object.

        Returns:
            A linkage created based on the data from the dict.

        Examples:
            .. code-block:: python

                input = [{
                    "id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }]
                linkage = Linkage.from_dict(input)
        """
        if isclass(cls):
            linkage = cls()
        else:
            assert isinstance(cls, Linkage)
            linkage = cls

        for linker_dict in data:
            new_linker = Linker.from_dict(linker_dict)
            linkage.add_linker(new_linker)

        return linkage
