from typing import List, Union
from warnings import warn
from xml.etree.ElementTree import Element, SubElement

from cobra.core.dictlist import DictList
from cobra.core.metabolite import Metabolite
from cobra.core.model import Model
from cobra.core.reaction import Reaction
from prettytable.prettytable import PrettyTable

from model_duplication.constraints.phase import Phase, Phases
from model_duplication.error import NameWarning, PhaseNotFound


# TODO: is cobra.Metabolite necessary?
class Transfer:
    """
    Additionally, Transfer includes the attribute 'metabolite', which refers
    to the metabolite that is transferred. Changing this attribute, it changes
    the corresponding internal identifier. It is recommended to use Phases
    when creating the Transfer to avoid KeyErrors

    Attributes:
        id (str): Internal identifier of the Transfer
        name (str): The internal name if the Transfer
        metabolite (str): The identifier of the involved metabolite
        reaction (Reaction): Internal Reaction of the Transfer
        source (str): The ID of the source phase.
        destination (str): The ID of the destination phase.
        lower_bound (int): The 'lower_bound' to be used for the reaction.
            For more information see ''lower_bound'' in :func:'cobra.Reaction'.
        upper_bound (int): The 'upper_bound' to be used for the reaction.
            For more information see ''lower_bound'' in :func:'cobra.Reaction'.
    """

    _metabolite: str
    _id: str = ""
    _name: str
    _reaction: Reaction
    _source: str
    _destination: str
    _lower_bound: int
    _upper_bound: int

    def __init__(
        self,
        metabolite: str,
        source: Union[Phase, str],
        destination: Union[Phase, str],
        lower_bound: int = 0,
        upper_bound: int = 1000,
    ):
        """
        Initializes the Transfer.

        Args:
            metabolite (str) = The identifier of the metabolite
            source: The ID of the source phase or the source
                phase itself.
            destination: The ID of the source phase or the
                source phase itself..
            lower_bound (int): The 'lower_bound' to be used for the reaction.
            upper_bound (int): The 'upper_bound' to be used for the reaction.
        """
        # TODO: Nomenclature for transfers.
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound
        self.source = source
        self.destination = destination

        self._id = f"TR_{metabolite}_{self.source}_{self.destination}"
        self._name = (
            f"Transfer for {metabolite} from {self.source} to"
            "{self.destination}"
        )
        self._metabolite = metabolite
        self._reaction = Reaction(
            self.id, self.name, "Transfer", lower_bound, upper_bound
        )

    @property
    def metabolite(self):
        return self._metabolite

    @metabolite.setter
    def metabolite(self, identifier: str):
        """
        Setter for metabolite. This method updates the internal name and id
        for the reaction.
        """
        self._metabolite = identifier
        self._id = f"TR_{identifier}_{self.source}_{self.destination}"
        self._title = (
            f"Transfer for {self.id} from {self.source} to "
            f"{self.destination}"
        )
        # TODO: create new reaction or rather change attributes?
        self._reaction = Reaction(
            self.id, self.name, "Transfer", self.lower_bound, self.upper_bound
        )

    @property
    def lower_bound(self):
        return self._lower_bound

    @lower_bound.setter
    def lower_bound(self, value: int):
        self._lower_bound = value

    @property
    def upper_bound(self):
        return self._upper_bound

    @upper_bound.setter
    def upper_bound(self, value: int):
        self._upper_bound = value

    @property
    def id(self):
        return self._id

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, phase: Union[Phase, str]):
        """
        Setter for attribute source. It is encouraged to use a 'Phase' rather
        than a string
        """
        if isinstance(phase, Phase):
            self._source = phase.id

        else:

            warn(
                "The use of strings is not recommended. Rather "
                "use a Phase to ensure an existing name",
                NameWarning,
            )
            self._source = phase

    @property
    def destination(self):
        return self._destination

    @destination.setter
    def destination(self, phase: Union[Phase, str]):
        """
        Setter for attribute destination. It is encouraged to use a 'Phase'
        rather than a string
        """
        if isinstance(phase, Phase):
            self._destination = phase.id

        else:

            warn(
                "The use of strings is not recommended. Rather "
                "use a Phase to ensure an existing name",
                NameWarning,
            )
            self._destination = phase

    @property
    def name(self):
        """Name of the reaction"""
        return self._name

    @property
    def reaction(self):
        """COBRApy Reaction of the transfer"""
        return self._reaction

    def to_xml(self) -> Element:

        element = Element("transfer")
        SubElement(element, "destination").set("refid", self.destination)
        SubElement(element, "source").set("refid", self.source)

        element.set("metabolite", self.metabolite)
        element.set("lower_bound", str(self.lower_bound))
        element.set("upper_bound", str(self.upper_bound))

        return element

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data["metabolite"],
            data["source"],
            data["destination"],
            int(data["lower_bound"]["refid"]),
            int(data["upper_bound"]["refid"]),
        )

    def __str__(self) -> str:
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


class Conveyance(DictList):
    """
    DictList with the Transfers. Refer to :py:class:`cobra.DictList`
    for its methods.
    """

    def apply(self, model: Model, phases: Phases) -> Model:
        """
        Returns a :py:class:`cobra.Model` including transfers reactions in the
        Conveyance.

        Args:
            model: The model to include the transfer reactions.
            phases: A phases object that contains all phases referenced by
                each individual Transfer.

        Returns:
            A :py:class:`cobra.model` that contains the Linker.
        """

        _model = model.copy()

        try:

            item: Transfer
            for item in self:

                try:
                    source: Phase = phases.phases.get_by_id(item.source)
                    destination: Phase = phases.phases.get_by_id(
                        item.destination
                    )

                except KeyError:
                    raise PhaseNotFound

                source_metabolite: Metabolite = _model.metabolites.get_by_id(
                    item.metabolite + "_" + item.source
                )
                destination_metabolite: Metabolite = (
                    _model.metabolites.get_by_id(
                        item.metabolite + "_" + item.destination
                    )
                )

                transfer = item.reaction
                transfer.add_metabolites(
                    {
                        source_metabolite: -destination.volume
                        * destination.timeframe,
                        destination_metabolite: source.volume
                        * source.timeframe,
                    }
                )
                _model.add_reactions([transfer])

            return _model

        except PhaseNotFound:
            warn(
                "One of the Phases in the Conveyance could not be found. "
                "Please revise that the source and destination of the "
                "transfers have existing phase identifiers",
                PhaseNotFound,
            )

            return model
