import re
from logging import getLogger
from typing import Optional, Union, Dict, List

from cobra import Model, Reaction, Solution
from cobra.core import get_solution
from cobra.util import fix_objective_as_constraint
from optlang import Objective, Variable
from optlang.symbolics import Zero

from cobra2d import Constraints

logger = getLogger(__name__)


def adjusted_pfba(
    constraints: Constraints,
    model: Model,
    fraction_of_optimum: float = 1.0,
    objective: Optional[Union[Dict, Objective]] = None,
    reactions: Optional[List[Reaction]] = None,
) -> Solution:
    """
    A customized version of the pFBA provided by COBRApy.
    It differs in that it takes into account the time periods and
    volumes defined through a Constraints object.

    Args:
        constraints: The Constraints object that defines the entire model.
        model: The COBRApy model created by the constraints object.
        fraction_of_optimum: The accuracy that the solution must have.
            More precisely, a constraint is defined that the original
            objective function must be greater than the product of
            fraction_of_optimum and flux of the original objective.
        objective: Additional objectives that can be defined in addition to
            minimizing the flux values.
        reactions: Reactions that should be minimized. The default are
            all "real" reactions. This means that transports and
            linkers are not minimized.

    Returns:

    """
    reactions = (
        model.reactions
        if reactions is None
        else model.reactions.get_by_any(reactions)
    )

    with model as copy:
        add_adjusted_pfba_objective(
            model=copy,
            constraints=constraints,
            objective=objective,
            fraction_of_optimum=fraction_of_optimum,
        )

        copy.slim_optimize(error_value=None)
        solution = get_solution(copy, reactions=reactions)
    return solution


def add_adjusted_pfba_objective(
    constraints: Constraints,
    model: Model,
    objective: Optional[Union[Dict, Objective]] = None,
    fraction_of_optimum: float = 1.0,
) -> None:
    if objective is not None:
        model.objective = objective

    if model.solver.objective.name == "_pfba_objective":
        raise ValueError("The model already has a pFBA objective.")

    fix_objective_as_constraint(model, fraction=fraction_of_optimum)

    model.objective = model.problem.Objective(
        Zero, direction="min", sloppy=True, name="_pfba_objective"
    )
    linear_coefficients: Dict[Variable, int] = {}

    # Reaction IDs are "<item_id>_<sub_model>_<time>" and both the item_id
    # and the sub_model may contain underscores, so the phase cannot be
    # recovered by splitting the reaction ID. Instead the reaction is matched
    # against the known phase IDs by suffix. Longer phase IDs are tried first
    # so the most specific match wins.
    phases_by_length = sorted(
        constraints.phases.phases,
        key=lambda phase: len(phase.id),
        reverse=True,
    )

    reaction: Reaction
    for reaction in model.reactions:
        # Skip linker and transfer reactions, they only exist in the context of
        # sub_models/time periods and are not weighted by a single phase. They
        # are identified by the '_lk_[...|...]' and '_tr_[...|...]' markers of
        # their naming convention.
        if re.search(r"_lk_.*\[.*\|.*\]$", reaction.id):
            continue
        if re.search(r"_tr_\[.*\|.*\]", reaction.id):
            continue

        matches = [
            phase
            for phase in phases_by_length
            if reaction.id.endswith(f"_{phase.id}")
        ]
        if not matches:
            raise KeyError(
                f"Reaction '{reaction.id}' could not be matched to any known "
                f"phase. Expected the ID to end with '_<phase_id>'."
            )

        # 'matches' is sorted longest phase ID first, so the most specific
        # phase wins. Multiple matches mean one phase ID is a suffix of another
        # (e.g. sub_models 'a' and 'x_a' both yield a '..._a_0' suffix), which
        # makes the ID ambiguous and points at a poor sub_model naming choice.
        if len(matches) > 1:
            logger.warning(
                "Reaction '%s' matches multiple phases %s; using the most "
                "specific one ('%s'). Consider renaming the sub_models to "
                "avoid one phase ID being a suffix of another.",
                reaction.id,
                [phase.id for phase in matches],
                matches[0].id,
            )
        phase = matches[0]
        coeff = phase.timeframe * phase.volume

        linear_coefficients[reaction.forward_variable] = coeff
        linear_coefficients[reaction.reverse_variable] = coeff

    model.objective.set_linear_coefficients(linear_coefficients)
