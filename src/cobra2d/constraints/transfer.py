"""
Implementation of the Transfer and Transfers classes.
"""

from __future__ import annotations

from typing import List, Union
from xml.etree.ElementTree import Element, SubElement

from cobra.core.model import Model

from cobra2d.constraints.phase import Phase, Phases
from cobra2d.constraints.transport import (
    Transport,
    Transports,
    split_phase_id,
)


class Transfer(Transport):
    """
    A transfer represents the transport of a metabolite from one sub_model to
    another within the same time period (spatial transport). In the model, it
    is represented by a pseudo reaction between the source and the
    destination phase.

    The reaction ID is derived from ``metabolite_id``, ``source`` and
    ``destination`` (see :py:attr:`reac_id`), so changing one of these
    attributes also changes the ID.

    Attributes:
        metabolite_id (str): The ID of the metabolite to be transported,
            without the phase suffix. It must match the ID of the metabolite
            in the model.
        source (str): The ID of the source phase.
        destination (str): The ID of the destination phase.
        lower_bound (float): The lower bound of the transfer reaction, see
            :py:attr:`cobra.Reaction.lower_bound`.
        upper_bound (float): The upper bound of the transfer reaction, see
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
        Initialize a Transfer.

        Args:
            metabolite_id: The ID of the metabolite to be transported, without
                the phase suffix. It must match the ID of the metabolite in
                the model.
            source: The source phase or its ID.
            destination: The destination phase or its ID.
            lower_bound: The lower bound of the transfer reaction, see
                :py:attr:`cobra.Reaction.lower_bound`.
            upper_bound: The upper bound of the transfer reaction, see
                :py:attr:`cobra.Reaction.upper_bound`.
        """

        super().__init__(
            metabolite_id=metabolite_id,
            source=source,
            destination=destination,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        # TODO: Nomenclature for transfers.

    def __str__(self) -> str:
        return super().__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Transfer):
            return False
        return super().__eq__(other)

    @property
    def reac_id(self) -> str:
        """The reaction ID following the naming convention for transfers.

        Transfers describe spatial transport, so source and destination differ
        in their sub_model but share the same time period. The resulting ID has
        the form ``<metabolite>_tr_[<source_sub_model>|<destination_sub_model>]_<time>``,
        e.g. ``STARCH_p_tr_[leaf|root]_1``.

        Raises:
            ValueError: If a phase ID cannot be split into ``<sub_model>_<time>``,
                or if source and destination do not share the same time period.
        """  # noqa: E501
        source_sub_model, source_time = split_phase_id(self.source)
        dest_sub_model, dest_time = split_phase_id(self.destination)

        if source_time != dest_time:
            raise ValueError(
                f"A transfer connects phases of the same time period, but "
                f"source '{self.source}' and destination '{self.destination}' "
                f"have different time periods ('{source_time}' vs. "
                f"'{dest_time}')."
            )

        return (
            f"{self.metabolite_id}_tr_"
            f"[{source_sub_model}|{dest_sub_model}]_{source_time}"
        )

    @property
    def reac_name(self) -> str:
        return (
            f"Transfer for {self.metabolite_id} "
            f"from {self.source} to {self.destination}"
        )

    def to_xml(self) -> Element:
        """
        Convert the transfer to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            the transfer.
        """
        element = Element("transfer")
        SubElement(element, "destination").set("refid", self.destination)
        SubElement(element, "source").set("refid", self.source)

        element.set("metabolite_id", self.metabolite_id)
        element.set("lower_bound", str(self.lower_bound))
        element.set("upper_bound", str(self.upper_bound))

        return element

    @classmethod
    def from_dict(cls, data: dict) -> Transfer:
        """
        Create a transfer from the data encoded in a dict.

        Args:
            data: A dict that contains the data required to create a
                transfer.

        Returns:
            A transfer created from the data in the dict.

        Examples:
            .. code-block:: python

                input = {
                    "metabolite_id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }
                transfer = Transfer.from_dict(input)
        """
        return cls(
            metabolite_id=data["metabolite_id"],
            source=data["source"]["refid"],
            destination=data["destination"]["refid"],
            lower_bound=float(data["lower_bound"]),
            upper_bound=float(data["upper_bound"]),
        )


class Transfers(Transports):
    """
    A collection of :py:class:`Transfer` objects that can be applied to a
    :py:class:`cobra.Model`.

    Transfers can be added with :py:meth:`append`, removed with
    :py:meth:`remove` and iterated over. The contained transfers are
    accessible as a list via the ``transfers`` property.
    """

    def __init__(self):
        super(Transfers, self).__init__()

    def __str__(self):
        """
        Create a table of all transfers.

        Returns:
            The metabolite ID, source, destination, lower bound and upper
            bound of each transfer as a table.
        """

        return super(Transfers, self).__str__()

    def __iter__(self):
        return super(Transfers, self).__iter__()

    def append(self, obj: Transfer):  # type: ignore
        """
        Add a transfer. A transfer that is already present is not added
        again, and a warning is issued instead.

        Args:
            obj: The transfer to be added.

        Raises:
            TypeError: If ``obj`` is not a :py:class:`Transfer`.
        """
        if isinstance(obj, Transfer):
            super(Transfers, self).append(obj)
        else:
            raise TypeError(f"{obj} is not of type Transfer cannot be added.")

    def remove(self, obj_pos: Union[Transport, int]):
        """
        Remove a transfer, given either as the transfer itself or as its
        position in the ``transfers`` list.

        Args:
            obj_pos: The transfer to be removed or its position.
        """
        super(Transfers, self).remove(obj_pos)

    @property
    def transfers(self):
        return self.transports

    def apply(self, model: Model, phases: Phases) -> Model:
        """
        Add a reaction for each transfer to a :py:class:`cobra.Model`.

        Args:
            model: The model to which the transfer reactions are added. It
                must already contain the phases, see
                :py:meth:`Phases.apply_phases`. The model is changed in
                place.
            phases: A phases object that contains all phases referenced by
                the transfers.

        Returns:
            The passed :py:class:`cobra.Model`, now containing the transfer
            reactions.
        """

        return super(Transfers, self).apply(model=model, phases=phases)

    def to_xml(self) -> Element:
        """
        Convert the transfers to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            The :py:class:`xml.etree.ElementTree.Element` representation of
            the transfers.
        """

        root = Element("transfers")

        item: Transfer
        for item in self:
            root.append(item.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Transfers:
        """
        Create a Transfers object from a list of dicts, each encoding a
        transfer.

        Args:
            data: A list of dicts, each containing the data required to
                create a transfer, see :py:meth:`Transfer.from_dict`.

        Returns:
            A Transfers object containing the transfers created from the
            dicts.

        Examples:
            .. code-block:: python

                input = [{
                    "metabolite_id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }]
                transfers = Transfers.from_dict(input)
        """
        container = Transfers()

        for dictionary in data:
            transfer = Transfer.from_dict(dictionary)
            container.append(transfer)

        return container
