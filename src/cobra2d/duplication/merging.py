"""Module for merging of COBRApy models
"""

from copy import deepcopy
from logging import getLogger
from typing import List

from cobra import DictList
from cobra.core import Group, Metabolite, Model, Reaction

logger = getLogger(__name__)


def _merge(model: Model, right: Model, suffix: str) -> Model:
    if not suffix or suffix.startswith("_"):
        raise ValueError(
            "Suffix must be non-empty and must not start with '_'"
        )

    model.merge(right=right, prefix_existing="failed_", objective="sum")

    # add unused metabolites and check if duplicates are created
    inactive_metabolites: DictList = DictList()

    for metabolite in right.metabolites:
        if len(metabolite.reactions) == 0:
            inactive_metabolites.append(deepcopy(metabolite))

    existing = inactive_metabolites.query(
        lambda met: met.id in model.metabolites
    )
    for metabolite in existing:
        metabolite.id = "{}{}".format("failed_", metabolite.id)

    model.add_metabolites(inactive_metabolites)

    # check that there are no duplicates marked with 'failed_'
    assert len(model.metabolites.query("failed_")) == 0
    assert len(model.reactions.query("failed_")) == 0

    # Two kinds of group belong to `right`: the sub_model's own groups, which
    # `_rename` suffixed with "_<suffix>", and the group representing the phase
    # itself, which is added after renaming and is therefore named exactly
    # "<suffix>". Both are carried over; comparing instead of using query()
    # avoids treating the suffix as a regex.
    group: Group
    for group in right.groups:
        if group.id != suffix and not group.id.endswith(f"_{suffix}"):
            continue
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


def _link_genes(
    model: Model, reactions: List[str], suffix: str, labels: List[str]
) -> Model:
    """
    Links the gene rule of a reaction to all of its copies in the sub_models.

    Args:
        model: The model containing every duplicated sub_model.
        reactions: The identifiers of the reactions in the original,
            unsuffixed model.
        suffix: The label of the sub_model the gene rules are taken from.
        labels: The labels of all sub_models present in ``model``. They are
            required to rebuild the exact reaction IDs: matching by prefix
            would let a reaction such as "PGK" also capture the unrelated
            "PGK_2_<label>", overwriting its gene rule.

    Returns:
        A copy of ``model`` in which every copy of a reaction carries the
        gene rule of its counterpart in the ``suffix`` sub_model.
    """

    _model = model.copy()

    reaction: str
    for reaction in reactions:
        try:
            reference_rule = model.reactions.get_by_id(
                f"{reaction}_{suffix}"
            ).gene_reaction_rule
        except KeyError:
            logger.warning(
                "No reaction '%s_%s' found to source the gene rule from; "
                "skipping gene linkage for '%s'.",
                reaction,
                suffix,
                reaction,
            )
            continue

        item: Reaction
        for label in labels:
            try:
                item = _model.reactions.get_by_id(f"{reaction}_{label}")
            except KeyError:
                continue

            item.gene_reaction_rule = reference_rule

    logger.info("Linkage of genes between multiple same reactions completed")

    return _model
