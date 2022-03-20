"""Module for merging of COBRApy models
"""
from logging import getLogger
from typing import List

from cobra.core import Group, Metabolite, Model, Reaction

logger = getLogger(__name__)


def _merge(model: Model, right: Model, suffix: str) -> Model:

    model.merge(right=right, prefix_existing="failed_")

    assert len(model.metabolites.query("failed_")) == 0
    assert len(model.reactions.query("failed_")) == 0
    assert len(model.genes) == len(right.genes)

    group: Group
    for group in right.groups.query(suffix):

        new_group = Group(id=group.id, name=group.name, kind=group.kind)
        new_group.notes = group.notes.copy()

        members = [
            model.reactions.get_by_id(item.id)
            for item in group.members
            if isinstance(item, Reaction)
        ] + [
            model.metabolites.get_by_id(item.id)
            for item in group.members
            if isinstance(item, Metabolite)
        ]

        assert len(members) == len(group.members)
        new_group.add_members(members)
        # FIXME: add debugs

        model.add_groups([new_group])

    # assert len(_model.groups) != len(right.groups)

    # FIXME: proper message
    logger.debug("Models merged")

    return model


def _link_genes(model: Model, reactions: List[str], suffix: str) -> Model:
    """
    Links the gene to the same reactions that are under different suffixes.
    Given reactions identifiers are passed as a list and the suffix of the
    main/first submodel
    """

    _model = model.copy()

    try:
        reaction: str
        for reaction in reactions:

            to_modify = _model.reactions.query(reaction)

            item: Reaction
            for item in to_modify:

                item.gene_reaction_rule = model.reactions.get_by_id(
                    f"{reaction}_{suffix}"
                ).gene_reaction_rule
                # TODO: add debug

    except Exception:

        # TODO: warning
        return model

    logger.info("Linkage of genes between multiple same reactions completed")

    return _model
