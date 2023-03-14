from typing import List, Dict

from cobra import Model, Reaction, Metabolite


def update_stoichiometry(
    model: Model, identifier: str, left: float = 1.0, right: float = 1.0
):
    """
    Updates given reactions with given left and right coefficients. Both
    coefficients must be positive. Only reactions with an specific SBO can be
    modified.
    """

    reaction: Reaction = model.reactions.get_by_id(identifier)
    assert (
        reaction.annotation["sbo"] == "SBO:0000167"
    ), f"Reaction {identifier} cannot be modified. (Wrong SBO)"

    metabolites: Dict[Metabolite, float] = reaction.metabolites

    for metabolite, coef in metabolites.items():
        if coef < 0:
            coef *= left

        else:
            coef *= right

        metabolites[metabolite] = coef

    reaction.add_metabolites(metabolites, combine=False)
    assert reaction.reversibility


def normalize(
    model: Model, transfers: List[str], left: float = 1, right: float = 1.0
):
    """
    This functions modifies each reaction in the transfers list taking the
    size of the organs into consideration. The coefficients for the reactions
    are calculated as:
    Left = 1
    Right = left / right
    This makes both sides of the equation equal
    """

    assert left > 0, "Left coefficient must be higher than 0"
    assert right > 0, "Right coefficient must be higher than 0"

    # conversion
    LEFT = 1
    RIGHT = left / right

    assert (
        LEFT * left == RIGHT * right
    ), "Both sides of the equation are not equal"

    for reaction in transfers:
        assert model.reactions.get_by_id(
            reaction
        ), f"{reaction} does not exist"

        update_stoichiometry(model, reaction, LEFT, RIGHT)
