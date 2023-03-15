from pathlib import Path
from typing import List

from cobra.core import Metabolite, Model, Reaction


def _read(file: Path) -> List[str]:
    # FIXME: identify csv and xls
    with open(file, "r") as f:
        lines = f.readlines()

    if not lines:
        # TODO: message
        raise Exception

    # FIXME: no commas
    return [line.replace("\n", "") for line in lines]


def _check_reactions(model: Model, elements: List[str]) -> bool:
    for element in elements:
        item = model.metabolites.query(element)

        if not item:
            # FIXME: raise problem
            return False

    return True


def read_file(model: Model, file: Path) -> List[str]:
    lines = _read(file)

    if _check_reactions(model, lines):
        return lines

    # FIXME: add debug
    raise Exception


# FIXME: find correct name for these types of reactions
def _create_reactions(
    model: Model, metabolites: List[str], left_suffix: str, right_suffix: str
) -> List[Reaction]:
    # FIXME: reaction type
    reaction_type = "Linker"

    inter_reactions: List[Reaction] = list()

    for metabolite in metabolites:
        right_metabolite: Metabolite = model.metabolites.get_by_id(
            f"{metabolite}_{right_suffix}"
        )
        left_metabolite: Metabolite = model.metabolites.get_by_id(
            f"{metabolite}_{left_suffix}"
        )

        # Build of reaction
        # FIXME: Name, compartment, type
        reaction = Reaction(
            id=f"{reaction_type}_{metabolite}_{left_suffix}_{right_suffix}",
            lower_bound=-1000,
            upper_bound=1000,
        )
        reaction.add_metabolites({left_metabolite: -1, right_metabolite: 1})
        assert reaction.bounds == (-1000, 1000)
        assert reaction not in model.reactions

        inter_reactions.append(reaction)
        # FIXME: add debug

    return inter_reactions
