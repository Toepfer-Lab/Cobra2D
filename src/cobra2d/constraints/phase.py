"""
Implementation of the Phase and Phases classes.
"""

from __future__ import annotations
import logging
import warnings
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
from cobra2d.error import GenesNotLinked, IdAlreadyInUse


class Phase:
    """
    A phase represents the combination of a sub_model (e.g. an organ) and a
    time period. It holds the ID of this combination together with the
    length of the time period and the volume of the sub_model. These are
    used both to build a :py:class:`Model` containing all phases and to
    scale the linker and transfer reactions between them. In addition, a
    phase can hold adjustments of individual reactions that only apply
    within this phase.

    Attributes:
        id (str): The ID of the phase.
        name (str): The name of the phase.
        light_dark (Literal["light","dark"]): The lighting conditions. This
            is metadata only: it is stored and written to XML, but not used
            when constructing the model.
        timeframe (int): The length of the time period of the phase.
        volume (int): The volume of the sub_model.
        model (Optional[Model]): A model assigned to this phase. If set,
            :py:meth:`Phases.apply_phases` (and therefore
            :py:meth:`Constraints.apply_to_model`, which forwards to it) uses
            this model for the phase instead of a copy of the passed model.
        reaction_settings (List[Reaction]): Reactions whose bounds replace
            those of the reactions with the same ID within this phase.
        objective_factor (float): A factor that scales the objective
            coefficients of this phase before summing all objective
            functions to form the final one. The coefficients are multiplied
            by ``objective_factor * timeframe * volume``, so the length of
            the time period and the volume are always taken into account.
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
            light_dark: The lighting conditions. Stored as metadata only.
            timeframe: The length of the time period of the phase.
            volume: The volume of the sub_model.
            name: The name of the phase.
            objective_factor: A factor that scales the objective
                coefficients of this phase, see :py:attr:`objective_factor`.
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
        Create a table describing the phase.

        Returns:
            The ID, name, volume and timeframe of the phase as a table.
        """
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        output.add_row([self.id, self.name, self.volume, self.timeframe])

        return output.get_string()

    def to_xml(self):
        """
        Convert the phase to an :py:class:`xml.etree.ElementTree.Element`.

        Returns:
            A :py:class:`xml.etree.ElementTree.Element` representing the
            phase.
        """
        element = Element("phase")

        element.set("id", self.id)
        element.set("light_dark", self.light_dark)
        element.set("name", self.name)
        element.set("objective_factor", str(self.objective_factor))
        element.set("timeframe", str(self.timeframe))
        element.set("volume", str(self.volume))

        for reaction in self.reaction_settings:
            child = Element("reaction")
            child.set("id", reaction.id)
            # COBRApy keeps whichever type a bound was given as, while the
            # schema stores bounds as doubles.
            child.set("lower_bound", str(float(reaction.lower_bound)))
            child.set("upper_bound", str(float(reaction.upper_bound)))

            element.append(child)

        return element

    def add_reaction(self, reaction: Reaction):
        """
        Add a reaction whose bounds are used to adjust the reaction with the
        same ID within the phase.

        Args:
            reaction: A reaction whose bounds are applied to the reaction
                with the same ID in the phase. Its ID must be the ID of the
                reaction in the original model, i.e. without the phase
                suffix.
        """
        self.reaction_settings.append(reaction)

    @classmethod
    def from_dict(cls, data: dict) -> Phase:
        """
        Create a phase from the data encoded in a dict.

        Args:
            data: A dict that contains the data required to create a phase.

        Returns:
            A phase created from the data in the dict.

        Examples:
            .. code-block:: python

                dictionary = {
                    "id": "id",
                    "volume": "4",
                    "light_dark": "light",
                    "timeframe": "4",
                    "objective_factor": "1",
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
            name=data.get("name", ""),
            light_dark=data["light_dark"],
            timeframe=int(data["timeframe"]),
            objective_factor=float(data.get("objective_factor", 1.0)),
        )

        if "reaction" not in data.keys():
            return output

        for reaction in data["reaction"]:
            new_reaction = Reaction(
                id=reaction["id"],
                lower_bound=float(reaction["lower_bound"]),
                upper_bound=float(reaction["upper_bound"]),
            )

            output.add_reaction(new_reaction)

        return output


class Phases:
    """
    The Phases class manages all phases defined for a model and creates the
    extended model that contains a copy of the model for each phase.

    Attributes:
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
        Create a table of all phases.

        Returns:
            The ID, name, volume and timeframe of each phase as a table.
        """
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        for phase in self.phases:
            output.add_row(
                [phase.id, phase.name, phase.volume, phase.timeframe]
            )

        return output.get_string()

    def clear_phases(self):
        """
        Remove all phases.
        """
        del self.phases
        self.phases = DictList()

    # TODO: maybe ability to add Iterators?
    def add_phase(self, phase: Phase):
        """
        Add a phase.

        Args:
            phase: The phase to be added.

        Raises:
            IdAlreadyInUse: If a phase with the same ID already exists.
        """

        if self.phases.has_id(phase.id):
            raise IdAlreadyInUse(phase.id)

        self.phases.append(phase)

    def remove_phase(self, phase: Union[Phase, str]):  # ToDo Change to @Param
        """
        Remove a single phase.

        Args:
            phase: The phase to be removed, or its ID.

        Raises:
            KeyError: If there is no phase with this ID.
        """

        id: str = phase.id if isinstance(phase, Phase) else phase

        if not self.phases.has_id(id):
            raise KeyError(f" There is no phase with ID: {id}")

        del self.phases[self.phases.index(id)]

    def apply_phases(
        self, model: Optional[Model] = None, link_genes: bool = False
    ) -> Model:
        """
        Apply the defined phases to a :py:class:`Model`.

        The model is copied once for each phase, and all copies are merged
        into a new model. If a phase already has a model assigned (see
        :py:attr:`Phase.model`), that model is used for the phase instead of
        ``model``. ``model`` itself is not changed.

        Args:
            model: The model to be copied for each phase. It may only be
                omitted if a model is assigned to every phase.
            link_genes: Whether the gene-reaction rules should be
                synchronized across all phases that are built from ``model``.
                Phases with their own model (set via :py:attr:`Phase.model`)
                are not linked and keep their own rules; a
                :py:class:`cobra2d.error.GenesNotLinked` warning lists them.

        Returns:
            A new model that consists of one copy of the original model per
            phase. The IDs of the reactions, metabolites and groups of a
            phase end with ``_<phase ID>``.

        Raises:
            ValueError: If ``model`` is None although there are phases
                without an assigned model.
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

        if link_genes and with_model:
            warnings.warn(
                GenesNotLinked(phase.id for phase in with_model),
                stacklevel=2,
            )

        for phase in with_model:
            # Guaranteed by the partition above, but not visible to mypy.
            assert phase.model is not None
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
        Convert the phases object to an :py:class:`Element`.

        Returns:
            An :py:class:`Element` representing the phases object.
        """

        root = Element("phases")

        for phase in self.phases:
            root.append(phase.to_xml())

        return root

    @classmethod
    def from_dict(cls, data: List[dict]) -> Phases:
        """
        Create a phases object from a list of dicts, each encoding a phase.

        Args:
            data: A list of dicts, each containing the data required to
                create a phase, see :py:meth:`Phase.from_dict`.

        Returns:
            A phases object containing the phases created from the dicts.

        Examples:
            .. code-block:: python

                input = [{
                    'id': 'leaf_0',
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
