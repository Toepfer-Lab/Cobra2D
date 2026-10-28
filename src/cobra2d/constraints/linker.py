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
from cobra2d.constraints.transport import (
    Transport,
    Transports,
    split_phase_id,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.level = 20


class Linker(Transport):
    """
    A linker reaction represents the transport of a metabolite from one time
    period to another within the same sub_model (temporal transport). In the
    model, it is represented by a pseudo reaction between the source and the
    destination phase.

    Attributes:
        metabolite_id (str): The ID of the metabolite to be transported,
            without the phase suffix. It must match the ID of the metabolite
            in the model.
        source (str): The ID of the source phase.
        destination (str): The ID of the destination phase.
        lower_bound (float): The lower bound of the linker reaction, see
            :py:attr:`cobra.Reaction.lower_bound`.
        upper_bound (float): The upper bound of the linker reaction, see
            :py:attr:`cobra.Reaction.upper_bound`.
    """

    def __init__(
        self,
        metabolite_id: str,
        source: Union[Phase, str],
        destination: Union[Phase, str],
        lower_bound: float = 0.0,
        upper_bound: float = 1000.0,
    ):
        """
        Initialize a Linker.

        Args:
            metabolite_id: The ID of the metabolite to be transported, without
                the phase suffix. It must match the ID of the metabolite in
                the model.
            source: The source phase or its ID.
            destination: The destination phase or its ID.
            lower_bound: The lower bound of the linker reaction, see
                :py:attr:`cobra.Reaction.lower_bound`.
            upper_bound: The upper bound of the linker reaction, see
                :py:attr:`cobra.Reaction.upper_bound`.
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
        Create a table describing the linker reaction.

        Returns:
            The metabolite ID, source, destination, lower bound and upper
            bound of the linker reaction as a table.
        """
        return super().__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Linker):
            return False
        return super().__eq__(other)

    @property
    def reac_id(self) -> str:
        """The reaction ID following the naming convention for linker
        reactions.

        Linker reactions describe temporal transport, so source and destination differ
        in their time period but share the same sub_model. The resulting ID has
        the form ``<metabolite>_lk_<sub_model>_[<origin_time>|<destination_time>]``,
        e.g. ``STARCH_p_lk_leaf_[1|2]``.

        Raises:
            ValueError: If a phase ID cannot be split into ``<sub_model>_<time>``,
                or if source and destination do not share the same sub_model.
        """  # noqa: E501
        source_sub_model, source_time = split_phase_id(self.source)
        dest_sub_model, dest_time = split_phase_id(self.destination)

        if source_sub_model != dest_sub_model:
            raise ValueError(
                f"A linker reaction connects phases of the same sub_model, "
                f"but source '{self.source}' and destination "
                f"'{self.destination}' have different sub_models "
                f"('{source_sub_model}' vs. "
                f"'{dest_sub_model}')."
            )

        return (
            f"{self.metabolite_id}_lk_{source_sub_model}_"
            f"[{source_time}|{dest_time}]"
        )

    @property
    def reac_name(self) -> str:
        return (
            f"Linker for {self.metabolite_id} "
            f"from {self.source} to {self.destination}"
        )

    def to_xml(self) -> Element:
        """
        Convert the linker reaction to an
        :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            a linker reaction.
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
        Create a linker reaction from the data encoded in a dict.

        Args:
            data: A dict that contains the data required to create a linker
                reaction.

        Returns:
            A linker reaction created from the data in the dict.

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
            lower_bound=float(data["lower_bound"]),
            upper_bound=float(data["upper_bound"]),
            destination=data["destination"]["refid"],
            source=data["source"]["refid"],
        )


class Linkage(Transports):
    """
    A collection of :py:class:`Linker` objects that can be applied to a
    :py:class:`cobra.Model`.

    Linker reactions can be added with :py:meth:`append`, removed with
    :py:meth:`remove` and iterated over. The contained linker reactions are
    accessible as a list via the ``linker`` property.
    """

    # ToDo change to Set? or to DictList
    # COMMENT: So far, the behavior of DictList works flawlessly. This would
    # remove the check for duplicates as long as the identifiers are not the
    # same.

    def __init__(self):
        """
        Initialize a Linkage.
        """
        super(Linkage, self).__init__()

    def __str__(self):
        """
        Create a table of all linker reactions.

        Returns:
            The metabolite ID, source, destination, lower bound and upper
            bound of each linker reaction as a table.
        """
        return super(Linkage, self).__str__()

    def __iter__(self):
        return super(Linkage, self).__iter__()

    def append(self, obj: Linker):  # type: ignore
        """
        Add a linker reaction. A linker reaction that is already present is
        not added again, and a warning is issued instead.

        Args:
            obj: The linker reaction to be added.

        Raises:
            TypeError: If ``obj`` is not a :py:class:`Linker`.
        """
        if isinstance(obj, Linker):
            super(Linkage, self).append(obj)
        else:
            raise TypeError(f"{obj} is not a Linker and cannot be added.")

    def add_linker(self, linker: Linker):
        """
        Add a linker reaction.

        Args:
            linker: The linker reaction to be added.

        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:meth:`Linkage.append` instead.
        """
        warnings.warn(
            "'add_linker' is deprecated and will be removed in "
            "version 1.0.0. Use 'linkage.append' instead.",
            DeprecationWarning,
        )

        self.append(obj=linker)

    def remove(self, obj_pos: Union[Linker, int]):  # type: ignore
        """
        Remove a linker reaction, given either as the linker reaction itself
        or as its position in the ``linker`` list.

        Args:
            obj_pos: The linker reaction to be removed or its position.
        """
        super(Linkage, self).remove(obj_pos)

    @property
    def linker(self):
        return self.transports

    def remove_linker(self, obj_pos: Union[Linker, int]):
        """
        Remove a linker reaction, given either as the linker reaction itself
        or as its position in the ``linker`` list.

        Args:
            obj_pos: The linker reaction to be removed or its position.

        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:meth:`Linkage.remove` instead.

        """
        warnings.warn(
            "'remove_linker' is deprecated and will be removed in "
            "version 1.0.0. Use 'linkage.remove' instead.",
            DeprecationWarning,
        )

        self.remove(obj_pos=obj_pos)

    def apply(self, model: Model, phases: Phases) -> Model:
        """
        Add each linker reaction to a :py:class:`cobra.Model`.

        Args:
            model: The model to which the linker reactions are added. It must
                already contain the phases, see :py:meth:`Phases.apply_phases`.
                The model is changed in place.
            phases: A phases object that contains all phases referenced by
                the linker reactions.

        Returns:
            The passed :py:class:`cobra.Model`, now containing the linker
            reactions.
        """

        return super(Linkage, self).apply(model=model, phases=phases)

    def apply_linkage(self, model: Model, phases: Phases) -> Model:
        """
        Add each linker reaction to a :py:class:`cobra.Model`.

        Args:
            model: The model to which the linker reactions are added.
            phases: A phases object that contains all phases referenced by
                the linker reactions.

        Returns:
            The passed :py:class:`cobra.Model`, now containing the linker
            reactions.

        Note:
            This method is deprecated and will be removed in version 1.0.0.
            Use :py:meth:`Linkage.apply` instead.
        """

        warnings.warn(
            "'apply_linkage' is deprecated and will be removed in "
            "version 1.0.0. Use 'linkage.apply' instead.",
            DeprecationWarning,
        )

        return self.apply(
            model=model,
            phases=phases,
        )

    def to_xml(self) -> Element:
        """
        Convert the linkage to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            the linkage.
        """

        root = Element("linkage")
        for linker in self.linker:
            root.append(linker.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Linkage:
        """
        Create a linkage from a list of dicts, each encoding a linker
        reaction.

        Args:
            data: A list of dicts, each containing the data required to
                create a linker reaction, see :py:meth:`Linker.from_dict`.

        Returns:
            A linkage containing the linker reactions created from the dicts.

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
