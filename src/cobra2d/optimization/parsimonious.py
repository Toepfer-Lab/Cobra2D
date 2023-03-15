import re
from typing import Optional, Union, Dict, List

from cobra import Model, Reaction, Solution
from cobra.core import get_solution
from cobra.util import fix_objective_as_constraint
from optlang import Objective, Variable
from optlang.symbolics import Zero

from cobra2d import Constraints


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

    reaction: Reaction
    for reaction in model.reactions:
        try:
            # ToDo clear identification for Linker (Linker and Amino acids )
            if re.match(r".*[^_]_L_[^_].*", reaction.id):
                continue
            if re.match(r"^TR_.*$", reaction.id):
                continue
        except IndexError:
            pass
        phase_id = reaction.id[reaction.id.rindex("_") + 1 :]  # noqa: E203
        phase = constraints.phases.phases.get_by_id(phase_id)
        coeff = phase.timeframe * phase.volume

        linear_coefficients[reaction.forward_variable] = coeff
        linear_coefficients[reaction.reverse_variable] = coeff

    model.objective.set_linear_coefficients(linear_coefficients)
