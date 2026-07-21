from importlib_resources import files, as_file
from unittest import TestCase

import cobra
from cobra import Configuration
from cobra.core import Group, Metabolite, Model, Reaction
from cobra.io import read_sbml_model

from cobra2d.duplication.duplication import _rename
from cobra2d.duplication.merging import _link_genes, _merge


class MergingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cobra_config = Configuration()
        cobra_config.solver = "glpk"

        textbook_raw = files(cobra.data).joinpath("textbook.xml.gz")
        with as_file(textbook_raw) as textbookXML:
            cls.textbook = read_sbml_model(str(textbookXML))

        ecoli_raw = files(cobra.data).joinpath("iJO1366.xml.gz")
        with as_file(ecoli_raw) as ecoliXML:
            cls.ecoli = read_sbml_model(str(ecoliXML))

    def test_cobra_merge(self):
        """Test the behavior of method Model.merge"""

        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()
        model.merge(right=submodel, prefix_existing="right_")

        # COBRApy only duplicates reactions
        self.assertEqual(len(model.metabolites.query("right_")), 0)
        self.assertEqual(len(model.groups.query("right_")), 0)
        self.assertEqual(len(model.genes.query("right_")), 0)

    def test__merge(self):
        """Test the behavior of merging models with new function"""

        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()

        for invalid_suffix in ("", "_X"):
            with self.subTest(suffix=invalid_suffix):
                with self.assertRaisesRegex(
                    ValueError,
                    "Suffix must be non-empty and must not start with '_'",
                ):
                    _merge(
                        model=model,
                        right=submodel,
                        suffix=invalid_suffix,
                    )

        # Grouping
        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()

        for item in (
            submodel.metabolites + submodel.reactions + submodel.groups
        ):
            item.id = f"{item.id}_X"

        model = _merge(model, submodel, "X")

        self.assertRaises(
            AssertionError,
            _merge,
            model=model.copy(),
            right=submodel.copy(),
            suffix="X",
        )

        self.assertEqual(len(model.reactions), len(submodel.reactions) * 2)
        self.assertEqual(len(model.groups), len(submodel.groups) * 2)
        self.assertEqual(len(model.metabolites), len(submodel.metabolites) * 2)

    def test__merge_keeps_phase_group(self):
        """A group named exactly after the suffix must survive the merge.

        `_rename` suffixes the sub_model's own groups with "_<suffix>", but
        the group representing the phase is added afterwards and is named
        exactly "<suffix>". Matching only on the "_<suffix>" ending silently
        dropped it, which emptied model.groups for the whole model.
        """

        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()

        for item in (
            submodel.metabolites + submodel.reactions + submodel.groups
        ):
            item.id = f"{item.id}_X"

        submodel.add_groups(
            [
                Group(
                    id="X",
                    name="All reactions and metabolites of Phase: X",
                    members=submodel.reactions + submodel.metabolites,
                    kind="partonomy",
                )
            ]
        )

        merged = _merge(model, submodel, "X")

        self.assertIn("X", [group.id for group in merged.groups])
        self.assertEqual(
            len(merged.groups.get_by_id("X").members),
            len(submodel.reactions) + len(submodel.metabolites),
        )

    def test__link_genes_does_not_match_by_prefix(self):
        """A reaction must not capture another one sharing its prefix.

        "PGK_2_<label>" starts with "PGK_", so matching by prefix gave it the
        gene rule of the unrelated reaction "PGK". Which of the two won
        depended on their order in model.reactions.
        """

        for order in (("PGK_2", "PGK"), ("PGK", "PGK_2")):
            with self.subTest(order=order):
                model = Model("prefix")
                left = Metabolite("a_c")
                right = Metabolite("b_c")

                rules = {"PGK": "g1", "PGK_2": "g2"}
                built = {}
                for reaction_id in order:
                    reaction = Reaction(reaction_id)
                    reaction.add_metabolites({left: -1, right: 1})
                    reaction.gene_reaction_rule = rules[reaction_id]
                    built[reaction_id] = reaction

                model.add_reactions([built[name] for name in order])

                duplicate = model.copy()
                _rename(duplicate, "leaf_0")

                linked = _link_genes(
                    duplicate,
                    [reaction.id for reaction in model.reactions],
                    "leaf_0",
                    ["leaf_0"],
                )

                for reaction_id, rule in rules.items():
                    self.assertEqual(
                        linked.reactions.get_by_id(
                            f"{reaction_id}_leaf_0"
                        ).gene_reaction_rule,
                        rule,
                    )

    def test__link_genes(self):
        """Checks the behavior for linking genes"""

        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()

        reactions = [reaction.id for reaction in model.reactions]

        for item in model.metabolites + model.reactions + model.groups:
            item.id = f"{item.id}_01"

        for item in (
            submodel.metabolites + submodel.reactions + submodel.groups
        ):
            item.id = f"{item.id}_02"

            if isinstance(item, Reaction):
                item.gene_reaction_rule = ""

        model.merge(right=submodel, prefix_existing="failed_")

        model = _link_genes(model, reactions, "01", ["01", "02"])

        self.assertEqual(len(model.genes), len(submodel.genes))

        for gene in model.genes:
            if not gene.reactions:
                continue

            self.assertEqual(
                len(gene.reactions) % 2, 0, f"{gene.id}\n{len(gene.reactions)}"
            )
