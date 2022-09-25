from importlib.resources import files, as_file
from unittest import TestCase

import cobra
from cobra import Configuration
from cobra.core import Model, Reaction
from cobra.io import read_sbml_model

from model_duplication.duplication.merging import _link_genes, _merge


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

        self.assertRaises(
            AssertionError, _merge, model=model, right=submodel, suffix=""
        )

        # Grouping
        model: Model = self.textbook.copy()
        submodel: Model = self.textbook.copy()

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

        model = _link_genes(model, reactions, "01")

        self.assertEqual(len(model.genes), len(submodel.genes))

        for gene in model.genes:

            if not gene.reactions:
                continue

            self.assertEqual(
                len(gene.reactions) % 2, 0, f"{gene.id}\n{len(gene.reactions)}"
            )
