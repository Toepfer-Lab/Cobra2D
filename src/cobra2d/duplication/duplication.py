"""Module for model duplication
"""

from logging import StreamHandler, getLogger
from typing import List, Optional, Union

from cobra.core import Gene, Group, Metabolite, Model, Reaction
from cobra.core.configuration import Configuration
from cobra.exceptions import OptimizationError
from cobra.util import linear_reaction_coefficients

import cobra2d
from cobra2d.duplication.merging import _merge, _link_genes

TOLERANCE = Configuration().tolerance

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.level = 20


def _rename(model: Model, suffix: str, objective_factor: float = 1.0):
    model_objective = {}
    for reaction, coeff in linear_reaction_coefficients(model).items():
        model_objective[reaction.id] = coeff

    item: Union[Metabolite, Reaction, Group, Gene]
    for item in model.metabolites + model.reactions + model.groups:
        if item.id:
            item.id = f"{item.id}_{suffix}"
            logger.debug(msg=f"Item renamed to {item.id}")

        else:
            logger.warning(
                msg=f"Item {id(item)} has a problem with its id. No suffix"
                + "was added"
            )

    new_objectives = {}
    for reaction_id, coeff in model_objective.items():
        reaction = model.reactions.get_by_id(f"{reaction_id}_{suffix}")
        new_objectives[reaction] = coeff * objective_factor

    model.objective = new_objectives


def _test(main: Model, submodel: Model) -> bool:
    passed = False

    # Copy original
    original = main.objective
    original_direction = main.objective_direction

    # Use objective from submodel
    main.objective = submodel.objective
    main.objective_direction = submodel.objective_direction

    try:
        # error_value=None makes slim_optimize return None instead of raising
        # when the problem is infeasible.
        value: Optional[float] = main.slim_optimize(error_value=None)

        if value is not None and abs(value) > TOLERANCE:
            passed = True

    except OptimizationError:
        passed = False

    # At the end revert
    main.objective = original
    main.objective_direction = original_direction

    return passed


def _main_placeholder(
    model: Model,
    labels: List[str],
    objective_factor: List[float],
    genes: bool = False,
) -> Model:
    _model = model.copy()
    _rename(
        model=_model, suffix=labels[0], objective_factor=objective_factor[0]
    )
    logger.info(f"New suffix '{labels[0]}' for model added")

    # The first sub_model forms the base of the merged model and is never
    # passed to _merge as `right`, so unlike the sub_models below its phase
    # group has to be added here.
    _model.add_groups(
        [
            Group(
                id=labels[0],
                name="All reactions and metabolites of Phase: " + labels[0],
                members=_model.reactions + _model.metabolites,
                kind="partonomy",
            )
        ]
    )

    for i, label in enumerate(labels[1:], 1):
        # Use copy of original to avoid 2n reactions
        submodel: Model = model.copy()
        _rename(
            model=submodel,
            suffix=f"{label}",
            objective_factor=objective_factor[i],
        )

        # Add all objects of the model to a group named after the label
        submodel.add_groups(
            [
                Group(
                    id=label,
                    name="All reactions and metabolites of Phase: " + label,
                    members=submodel.reactions + submodel.metabolites,
                    kind="partonomy",
                )
            ]
        )

        _model = _merge(model=_model, right=submodel, suffix=label)

        # update objective function
        # TODO deprecated ?
        if not _test(_model, submodel):
            raise Exception(f"Test for submodel {submodel.id}_{label} failed.")

        else:
            logger.debug(f"Test for submodel {submodel.id}_{label} passed")

        logger.info(f"Iteration {i} for '{label}' completed")

    if genes:
        reactions: List[str] = [item.id for item in model.reactions]

        _model = _link_genes(_model, reactions, labels[0], labels)

    # Meta-data
    _model.notes["submodels-info"] = (
        f"Modified with Cobra2D version {cobra2d.__version__}"
    )
    _model.notes["submodels"] = ",".join(labels)

    logger.info(f"Model {model.id} successfully modified")

    return _model
