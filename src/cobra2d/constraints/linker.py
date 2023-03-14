"""
Implementation of the Linker and Linkage classes.
"""

from __future__ import annotations

import logging
import warnings
from inspect import isclass
from typing import List, Union
from xml.etree.ElementTree import Element, SubElement

from cobra import Model

from cobra2d.constraints.phase import Phase, Phases
from cobra2d.constraints.transport import Transport, Transports

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.level = 20


class Linker(Transport):
    """
    Linker is a Subclass of Transport and represents a transition of a
    Metabolite from one Phase to another. Phases itself define a fixed time
    period in a fixed organ. Using this information, a pseudo reaction can be
    created representing the transition between two such phases.

    Attributes:
        metabolite_id: The ID to be used for the metabolite. This should match
                the ID of the metabolite in the model.
        source (str): The ID of the source phase.
        destination (str): The ID of the destination phase.
        lower_bound (int): The 'lower_bound' to be used for the reaction.
            For more information see 'lower_bound' in
            :py:func:`cobra.Reaction`.
        upper_bound (int): The 'upper_bound' to be used for the reaction.
            For more information see 'lower_bound' in
            :py:func:`cobra.Reaction`.
    """

    def __init__(
        self,
        metabolite_id: str,
        source: Union[Phase, str],
        destination: Union[Phase, str],
        lower_bound: int = 0,
        upper_bound: int = 1000,
    ):
        """
        Initialize a Linker.

        Args:
            metabolite_id: The ID to be used for the metabolite. This should
                match the ID of the metabolite in the model.
            source: The ID of the source phase or the source
                phase itself.
            destination: The ID of the source phase or the
                source phase itself.
            lower_bound: The 'lower_bound' to be used for the reaction.
                For more information see :py:attr:`cobra.Reaction.lower_bound`
                in :py:func:`cobra.Reaction`.
            upper_bound: The 'upper_bound' to be used for the reaction.
                For more information see :py:attr:`lower_bound` in
                :py:class:`cobra.Reaction.`.
        """
        super().__init__(
            metabolite_id=metabolite_id,
            source=source,
            destination=destination,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

    def __str__(self) -> str:
        """
        The toString method of the Linker class.
        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of the linker object as a formatted string.

        """
        return super().__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Linker):
            return False
        return super().__eq__(other)

    @property
    def reac_id(self) -> str:
        return f"{self.metabolite_id}_L_{self.source}_{self.destination}"

    @property
    def reac_name(self) -> str:
        return (
            f"Linker for {self.metabolite_id} "
            f"from {self.source} to {self.destination}"
        )

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

        element.set("metabolite_id", self.metabolite_id)
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
            A linker based on the data from the dict.

        Examples:
            .. code-block:: python

                dictionary = {
                    "metabolite_id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }
                linker = Linker.from_dict(dictionary)
        """
        return cls(
            metabolite_id=data["metabolite_id"],
            lower_bound=int(data["lower_bound"]),
            upper_bound=int(data["upper_bound"]),
            destination=data["destination"]["refid"],
            source=data["source"]["refid"],
        )


class Linkage(Transports):
    """
    Linkage as a class represents multiple Linker. Furthermore it implements
    the applying of Linkers to a cobra.model.

    """

    # ToDo change to Set? or to DictList
    # COMMENT:So far, the behavior of DictList works flawlessly. This would
    # remove the check for duplicates as long the identifiers are not the same

    def __init__(self):
        """
        Initialize a Linkage.
        """
        super(Linkage, self).__init__()

    def __str__(self):
        """
        The toString method of the Linkage class.

        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of all linker objects as a formatted string.
        """
        return super(Linkage, self).__str__()

    def __iter__(self):
        return super(Linkage, self).__iter__()

    def append(self, obj: Linker):  # type: ignore
        """
        Adds linker to the linkage class.

        Args:
            obj: The linker to be added.
        """
        if isinstance(obj, Linker):
            super(Linkage, self).append(obj)
        else:
            raise TypeError(f"{obj} is not of type linker cannot be added.")

    def add_linker(self, linker: Linker):
        """
        Adds linker to the linkage class.

        Args:
            linker: The linker to be added.

        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:method:`linkage.linker.append` instead.
        """
        warnings.warn(
            "'add_linker' is deprecated and will be removed in "
            "version 1.0.0. Use 'linkage.append' instead.",
            DeprecationWarning,
        )

        self.append(obj=linker)

    def remove(self, obj_pos: Union[Linker, int]):  # type: ignore
        """
        Function to remove a linker. Either the position of the linker in the
        :py:attr:`linkage.linker` list can be specified or the respective
        linker.

        Args:
            obj_pos: The position of the linker object to be deleted or
                itself.

        """
        super(Linkage, self).remove(obj_pos)

    @property
    def linker(self):
        return self.transports

    def remove_linker(self, obj_pos: Union[Linker, int]):
        """
        Function to remove a linker. Either the position of the linker in the
        :py:attr:`linkage.linker` list can be specified or the respective
        linker.

        Args:
            obj_pos: The position of the linker object to be deleted or
                itself.

        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:method:`linkage.linker.remove` instead.

        """
        warnings.warn(
            "'add_linker' is deprecated and will be removed in "
            "version 1.0.0. Use `linkage.append` instead.",
            DeprecationWarning,
        )

        self.remove(obj_pos=obj_pos)

    def apply(self, model: Model, phases: Phases) -> Model:
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

        return super(Linkage, self).apply(model=model, phases=phases)

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
        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:method:`linkage.linker.apply` instead.
        """

        warnings.warn(
            "'apply_linkage' is deprecated and will be removed in "
            "version 1.0.0. Use `linkage.linker.apply` instead.",
            DeprecationWarning,
        )

        return self.apply(
            model=model,
            phases=phases,
        )

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
                    "metabolite_id": "id",
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
            linkage.append(new_linker)

        return linkage
