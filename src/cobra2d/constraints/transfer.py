from __future__ import annotations

from typing import List, Union
from xml.etree.ElementTree import Element, SubElement

from cobra.core.model import Model

from cobra2d.constraints.phase import Phase, Phases
from cobra2d.constraints.transport import Transport, Transports


class Transfer(Transport):
    """
    Representation of a Transfer. It includes the attribute 'metabolite',
    which refers to the metabolite that is transferred. Changing this
    attribute, it changes the corresponding internal identifier. It is
    recommended to use Phases when creating the Transfer to avoid KeyErrors

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
        Initializes the Transfer.

        Args:
            metabolite_id (str) = The identifier of the metabolite
            source: The ID of the source phase or the source
                phase itself.
            destination: The ID of the source phase or the
                source phase itself..
            lower_bound (int): The 'lower_bound' to be used for the reaction.
            upper_bound (int): The 'upper_bound' to be used for the reaction.
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
        return f"TR_{self.metabolite_id}_{self.source}_{self.destination}"

    @property
    def reac_name(self) -> str:
        return (
            f"Transfer for {self.metabolite_id} "
            f"from {self.source} to {self.destination}"
        )

    def to_xml(self) -> Element:
        element = Element("transfer")
        SubElement(element, "destination").set("refid", self.destination)
        SubElement(element, "source").set("refid", self.source)

        element.set("metabolite", self.metabolite_id)
        element.set("lower_bound", str(self.lower_bound))
        element.set("upper_bound", str(self.upper_bound))

        return element

    @classmethod
    def from_dict(cls, data: dict) -> Transfer:
        """
        Creates an object from given dictionary

        Args:
            data: A dict that contains the necessary data to create
                a transport.

        Returns:
            A transport based on the data from the dict.

        Examples:
            .. code-block:: python

                input = {
                    "metabolite_id": "id",
                    "lower_bound": "4",
                    "upper_bound": "500",
                    "destination": {"refid": "destination"},
                    "source": {"refid": "source"}
                }
                transfers = Transfers.from_dict(input)
        """
        return cls(
            metabolite_id=data["metabolite"],
            source=data["source"]["refid"],
            destination=data["destination"]["refid"],
            lower_bound=int(data["lower_bound"]),
            upper_bound=int(data["upper_bound"]),
        )


class Transfers(Transports):
    """
    DictList with the Transfers. Refer to :py:class:`cobra.DictList`
    for its methods.

    Additionally it includes the following methods: apply, from_dict
    and to_xml
    """

    def __init__(self):
        super(Transfers, self).__init__()

    def __str__(self):
        """
        The toString method of the Transfer class.

        Returns:
            The ID, name, source, destination, lower bound and upper
            bound of all linker objects as a formatted string.
        """

        return super(Transfers, self).__str__()

    def __iter__(self):
        return super(Transfers, self).__iter__()

    def append(self, obj: Transfer):  # type: ignore
        """
        Adds a transfer to the Transfers class.

        Args:
            obj: The transfer to be added.

        """
        if isinstance(obj, Transfer):
            super(Transfers, self).append(obj)
        else:
            raise TypeError(f"{obj} is not of type Transfer cannot be added.")

    def remove(self, obj_pos: Union[Transport, int]):
        """
        Function to remove a transfer. Either the position of the transfer in
        the :py:attr:`linkage.transfer` list can be specified or the respective
        linker.

        Args:
            obj_pos: The position of the transfer object to be deleted or
                itself."""
        super(Transfers, self).remove(obj_pos)

    @property
    def transfers(self):
        return self.transports

    def apply(self, model: Model, phases: Phases) -> Model:
        """
        Returns a :py:class:`cobra.Model` including transfers reactions in the
        Transfers object.

        Args:
            model: The model to include the transfer reactions.
            phases: A phases object that contains all phases referenced by
                each individual Transfer.

        Returns:
            A :py:class:`cobra.model` that contains the transfers.
        """

        return super(Transfers, self).apply(model=model, phases=phases)

    def to_xml(self) -> Element:
        """
        Converts Transfers to an :py:class:`xml.etree.ElementTree.Element`.
        """

        root = Element("Transfers")

        item: Transfer
        for item in self:
            root.append(item.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Transfers:
        """
        Creates a Transfers object based on the data encoded in a dict.

        Args:
            data: A list of dicts that contain the necessary data to create a
                transfer object.

        Returns:
            A transfers-container created based on the data from the dict.

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
