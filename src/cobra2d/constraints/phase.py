"""
Implementation of the phase and Phases classes.

"""
from __future__ import annotations
import logging
from inspect import isclass
from typing import List, Union, Optional
from xml.etree.ElementTree import Element

from cobra import DictList, Model, Reaction
from cobra.core import Group
from cobra.util import linear_reaction_coefficients
from prettytable import PrettyTable
from typing_extensions import Literal

from cobra2d.duplication.duplication import (
    _main_placeholder,
    _rename,
    _test,
)
from cobra2d.duplication.merging import _merge
from cobra2d.error import IdAlreadyInUse


class Phase:
    """
    The phase class defines the representation of an organ, period combination.
    Hereby phase contains all information like the id but also the time frame
    of the considered period and the volume of the organ. This information is
    not only used for the creation of a :py:class:`Model` with these
    organ-period combinations but also for the normalization of for example
    linker reactions. Furthermore, phases also contain individual adjustments
    of reactions within the phase.

    Attributes:
        id(str): The ID of the phase.
        name(str): The name of the phase.
        light_dark(Literal["light","dark"]): Definition of the lighting
            conditions.
        volume(int): The volume of the organ.
        model(Model): This attribute can be used to assign a model to the
            phase. This guarantees that :py:func:`apply_phases` does not create
            a duplicate of the passed model but uses the one associated with
            the phase.
        reaction_settings(Reaction): Definition of reactions to be adjusted
            identically to those defined here within the phase.
        objective_factor(float): A factor that scales the value of the
            objective_function of this phase before summing all objective
            functions to form the final one.
    """

    id: str
    name: str

    # ToDo light_dark maybe add None if not using
    light_dark: Literal["light", "dark"]
    timeframe: int
    volume: int
    model: Optional[Model]
    reaction_settings: List[Reaction]
    objective_factor: float

    def __init__(
        self,
        id: str,
        # COMMENT: this might be fixed if using tags
        light_dark: Literal["light", "dark"],
        timeframe: int = 1,
        volume: int = 1,
        name: str = "",
        objective_factor=1.0,
    ):
        """
        Initialize a Phase.

        Args:
            id: The ID to be used for the phase.
            light_dark: Definition of the lighting
                conditions and thus the energy consumed for maintenance??
            timeframe:
            volume: The volume of the organ.
            name: The name of the phase.
        """
        self.id = id
        self.volume = volume
        self.name = name
        self.light_dark = light_dark
        self.timeframe = timeframe
        self.reaction_settings = []
        self.model = None
        self.objective_factor = objective_factor

    def __str__(self):
        """
        The toString method of the Phases class. It creates a tabular based
        representation of the Phases class.

        Returns:
            The ID, name, volume and time frame of each phase in a table form
            as a string.


        """
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        output.add_row([self.id, self.name, self.volume, self.timeframe])

        return output.get_string()

    def to_xml(self):
        """
        Converts a Phase to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
        A :py:class:`xml.etree.ElementTree.Element` representing a phase.
        """
        element = Element("phase")

        element.set("id", self.id)
        element.set("light_dark", self.light_dark)
        element.set("name", self.name)
        element.set("timeframe", str(self.timeframe))
        element.set("volume", str(self.volume))

        for reaction in self.reaction_settings:
            child = Element("reaction")
            child.set("id", reaction.id)
            child.set("lower_bound", str(reaction.lower_bound))
            child.set("upper_bound", str(reaction.upper_bound))

            element.append(child)

        return element

    def add_reaction(self, reaction: Reaction):
        """
        Function to add a reaction whose parameters are used to adjust
        reactions within the phase.

        Args:
            reaction: A reaction whose parameters are applied to the reaction
            with identical name in the phase. The name must not contain the
            phase ID.
        """
        self.reaction_settings.append(reaction)

    @classmethod
    def from_dict(cls, data: dict) -> Phase:
        """
        Creates a phase object based on the data encoded in a dict.

        Args:
            data: A dict that contains the necessary data to create a phase.

        Returns:
            A phase created based on the data from the dict.

        Examples:
            .. code-block:: python

                dictionary = {
                    "id": "id",
                    "volume": "4",
                    "light_dark": "500",
                    "timeframe": "4",
                    "reaction":[{
                        "id":"reactions_id",
                        "lower_bound": "3",
                        "upper_bound": "23",
                    }]
                }
                phase = Phase.from_dict(dictionary)

        """
        output = cls(
            id=data["id"],
            volume=int(data["volume"]),
            name=data["name"],
            light_dark=data["light_dark"],
            timeframe=int(data["timeframe"]),
        )

        if "reaction" not in data.keys():
            return output

        for reaction in data["reaction"]:
            new_reaction = Reaction(
                id=reaction["id"],
                lower_bound=reaction["lower_bound"],
                upper_bound=reaction["upper_bound"],
            )

            output.add_reaction(new_reaction)

        return output


class Phases:
    """
    The Phases class manages all phases defined for a model. Furthermore,
    it is responsible for creating an extended model based on the phases.


    Attributes
        phases (DictList[Phase]): A list that contains the individual phases.

    """

    phases: DictList[Phase]

    def __init__(self):
        """
        Initialize Phases.
        """
        self.phases = DictList()

    def __str__(self):
        """
        The toString method of the Phases class. It creates a tabular based
        representation of the Phases class.

        Returns:
            The ID, name, volume and time frame of each phase in a table form
            as a string.


        """
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        for phase in self.phases:
            output.add_row(
                [phase.id, phase.name, phase.volume, phase.timeframe]
            )

        return output.get_string()

    def clear_phases(self):
        """
        Method to delete all phases.
        """
        del self.phases
        self.phases = DictList()

    # TODO: maybe ability to add Iterators?
    def add_phase(self, phase: Phase):
        """
        Method to add a phase to the Phases object.

        Args:
            phase: The phase object to be added.
        """

        if self.phases.has_id(phase.id):
            raise IdAlreadyInUse(phase.id)

        self.phases.append(phase)

    def remove_phase(self, phase: Union[Phase, str]):  # ToDo Change to @Param
        """
        Method to remove individual phases.

        Args:
            phase: The phase itself or its position in the internal list
            that is to be removed

        """

        id: str = phase.id if isinstance(phase, Phase) else phase

        if not self.phases.has_id(id):
            raise KeyError(f" There is no phase with ID: {id}")

        del self.phases[self.phases.index(id)]

    def apply_phases(
        self, model: Optional[Model] = None, link_genes: bool = False
    ) -> Model:
        """
        Method to apply the previously defined phases to a
        :py:class:`Model`. The :py:class:`Model` is copied several
        times and each resulting :py:class:`Model` corresponds to a
        phase or time and organ combination. If a phase contains a
        :py:class:`Model`, then that :py:class:`Model` will be used
        and not the passed :py:class:`Model`. The extended
        :py:class:`Model` is returned.

        Args:
            model: The model to which the phases are to be applied.
            link_genes: Boolean that determines whether the already existing
                genes should be assigned to the differently named reactions
                when duplicating the models.

        Returns:
            A Cobra model that consists of multiple copies of the original,
            each assigned to a phase. The name of the elements that belong to
            a phase ends with "_nameOfThePhase".
        """
        with_model: List[Phase] = []
        without_model: List[Phase] = []
        new_model = Model()

        for phase in self.phases:
            (without_model if phase.model is None else with_model).append(
                phase
            )

        phase_names = []
        objective_factor = []

        for phase in without_model:
            phase_names.append(phase.id)
            objective_factor.append(
                phase.objective_factor * phase.timeframe * phase.volume
            )

        if without_model:
            if model is None:
                logging.error(
                    "There are phases without assigned models, but "
                    "no model was passed that could be used as "
                    "default model."
                )

                raise ValueError(
                    "Model was None although there were phases "
                    "without model."
                )

            new_model = _main_placeholder(
                model=model,
                labels=phase_names,
                genes=link_genes,
                objective_factor=objective_factor,
            )

        for phase in with_model:
            copy = phase.model.copy()

            # ToDo duplicate code from _main_placeholder should be refactored
            _rename(
                copy,
                phase.id,
                phase.objective_factor * phase.timeframe * phase.volume,
            )

            # Add all objects of the model to a group named after the label
            copy.add_groups(
                [
                    Group(
                        id=phase.id,
                        name=f"All reactions and metabolites of "
                        f"Phase: {phase.id}",
                        members=copy.reactions + copy.metabolites,
                        kind="partonomy",
                    )
                ]
            )
            new_model = _merge(new_model, copy, phase.id)
            if not _test(new_model, copy):
                raise Exception(f"Test for phase {copy.id} failed.")

            # ToDo Genes wont be connected? no knowledge if Genes are identical

        model_objective = {}
        for reaction, coeff in linear_reaction_coefficients(new_model).items():
            model_objective[reaction.id] = coeff

        for phase in self.phases:
            for reaction in phase.reaction_settings:
                reaction2adjust: Reaction = new_model.reactions.get_by_id(
                    f"{reaction.id}_{phase.id}"
                )
                reaction2adjust.lower_bound = reaction.lower_bound
                reaction2adjust.upper_bound = reaction.upper_bound

        return new_model

    def to_xml(self) -> Element:
        """
        Converts a linkage to an :py:class:`Element`.

        Returns:
            A :py:class:`Element` representing a phases
            object.
        """

        root = Element("phases")

        for phase in self.phases:
            root.append(phase.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Phases:
        """
        Creates a phases object based on the data encoded in a dict.

        Args:
            data: A list of dicts that contain the necessary data to create a
                phases object.

        Returns:
            A phases object created based on the data from the dict.

        Examples:
            .. code-block:: python

                input = [{
                    'id': 'leaf-0',
                    'volume': 1,
                    'name': '',
                    'light_dark': 'light',
                    'timeframe': 2,
                    'reaction': [{
                        'id': 'ATPM',
                        'lower_bound': 456,
                        'upper_bound': 765
                        }]
                    },]

                phases = Phases.from_dict(input)
        """
        if isclass(cls):
            phases = cls()

        else:
            assert isinstance(cls, Phases)
            phases = cls

        for phase_dict in data:
            new_phase = Phase.from_dict(phase_dict)
            phases.add_phase(new_phase)

        return phases
