import unittest

from cobra.core import Model, Reaction
from cobra.test import create_test_model

from model_duplication.duplication.merging import _link_genes, _merge


class MergingTest(unittest.TestCase):
    def test_cobra_merge(self):
        """Test the behavior of method Model.merge"""

        model: Model = create_test_model("textbook")
        submodel: Model = create_test_model("textbook")
        model.merge(right=submodel, prefix_existing="right_")

        # COBRApy only duplicates reactions
        self.assertEqual(len(model.metabolites.query("right_")), 0)
        self.assertEqual(len(model.groups.query("right_")), 0)
        self.assertEqual(len(model.genes.query("right_")), 0)

    def test__merge(self):
        """Test the behavior of merging models with new function"""

        model: Model = create_test_model("textbook")
        submodel: Model = create_test_model("textbook")

        self.assertRaises(
            AssertionError, _merge, model=model, right=submodel, suffix=""
        )

        # Grouping
        model: Model = create_test_model("textbook")
        submodel: Model = create_test_model("textbook")

        for item in (
            submodel.metabolites + submodel.reactions + submodel.groups
        ):

            item.id = f"{item.id}_X"

        model = _merge(model, submodel, "_X")

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

    def test__link_genes(self):
        """Checks the behavior for linking genes"""

        model: Model = create_test_model("textbook")
        submodel: Model = create_test_model("textbook")

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

        model = _link_genes(model, reactions, "01")

        self.assertEqual(len(model.genes), len(submodel.genes))

        for gene in model.genes:

            if not gene.reactions:
                continue

            self.assertEqual(
                len(gene.reactions) % 2, 0, f"{gene.id}\n{len(gene.reactions)}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)
