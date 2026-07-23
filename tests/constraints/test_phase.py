from unittest import TestCase
from xml.etree.ElementTree import Element

import cobra
from cobra import DictList, Metabolite, Model, Reaction
from cobra.io import read_sbml_model
from cobra.util import linear_reaction_coefficients
from importlib_resources import files, as_file

from cobra2d.constraints.phase import Phase, Phases
from cobra2d.error import GenesNotLinked


class TestPhase(TestCase):
    def test_create(self):
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        self.assertEqual(phase.id, "test_id")
        self.assertEqual(phase.light_dark, "light")
        self.assertEqual(phase.timeframe, 7)
        self.assertEqual(phase.volume, 3)

    def test_toString(self):
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        string = str(phase)
        expected = (
            "+---------+------+--------+-----------+\n"
            "|  Phase  | Name | Volume | Timeframe |\n"
            "+---------+------+--------+-----------+\n"
            "| test_id |      |   3    |     7     |\n"
            "+---------+------+--------+-----------+"
        )
        self.assertEqual(string, expected)

    def test_to_xml(self):
        phase = Phase(id="test_id", light_dark="light", objective_factor=0.5)

        xml = phase.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "phase")
        self.assertEqual(
            xml.attrib,
            {
                "id": "test_id",
                "volume": "1",
                "name": "",
                "light_dark": "light",
                "timeframe": "1",
                "objective_factor": "0.5",
            },
        )
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)

    def test_from_dict(self):
        dic = {
            "id": "test_id",
            "volume": "7",
            "name": "",
            "light_dark": "dark",
            "timeframe": "13",
            "objective_factor": "0.5",
            "reaction": [
                {"id": "R1", "lower_bound": "-1.5", "upper_bound": "1000"}
            ],
        }

        phase = Phase.from_dict(dic)

        self.assertEqual(phase.id, "test_id")
        self.assertEqual(phase.light_dark, "dark")
        self.assertEqual(phase.timeframe, 13)
        self.assertEqual(phase.volume, 7)
        self.assertEqual(phase.objective_factor, 0.5)

        self.assertEqual(len(phase.reaction_settings), 1)
        reaction = phase.reaction_settings[0]
        self.assertEqual(reaction.id, "R1")
        self.assertEqual(reaction.lower_bound, -1.5)
        self.assertEqual(reaction.upper_bound, 1000)

    def test_from_dict_uses_the_defaults_of_the_schema(self):
        """Attributes the schema declares a default for may be omitted."""
        phase = Phase.from_dict(
            {
                "id": "test_id",
                "volume": "1",
                "light_dark": "dark",
                "timeframe": "1",
            }
        )

        self.assertEqual(phase.name, "")
        self.assertEqual(phase.objective_factor, 1.0)


class TestPhases(TestCase):
    @classmethod
    def setUpClass(cls):
        textbook_raw = files(cobra.data).joinpath("textbook.xml.gz")
        with as_file(textbook_raw) as textbookXML:
            cls.textbook = read_sbml_model(str(textbookXML))

    def test_create(self):
        phases = Phases()

        self.assertIsInstance(phases, Phases)
        self.assertIsInstance(phases.phases, DictList)

    def test_toString(self):
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        phases.add_phase(phase)

        string = str(phases)
        expected = (
            "+---------+------+--------+-----------+\n"
            "|  Phase  | Name | Volume | Timeframe |\n"
            "+---------+------+--------+-----------+\n"
            "| test_id |      |   3    |     7     |\n"
            "+---------+------+--------+-----------+"
        )

        self.assertIsInstance(string, str)
        self.assertEqual(expected, string)

    def test_clear_phases(self):
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        phases.add_phase(phase)

        self.assertEqual(1, len(phases.phases))
        phases.clear_phases()
        self.assertIsInstance(phases.phases, DictList)
        self.assertEqual(0, len(phases.phases))

    def test_add_phase(self):
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        self.assertEqual(0, len(phases.phases))
        phases.add_phase(phase)
        self.assertEqual(1, len(phases.phases))
        self.assertEqual(phase, phases.phases[0])

    def test_remove_phase(self):
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        phases.add_phase(phase)
        self.assertEqual(1, len(phases.phases))
        phases.remove_phase(phase)
        self.assertEqual(0, len(phases.phases))

        phases.add_phase(phase)
        self.assertEqual(1, len(phases.phases))
        phases.remove_phase(phase.id)
        self.assertEqual(0, len(phases.phases))

    def test_apply_phases(self):
        model: Model = self.textbook.copy()
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        phases.add_phase(phase)
        new_model = phases.apply_phases(model)

        for metabolite in model.metabolites:
            new_metabolite: Metabolite = new_model.metabolites.get_by_id(
                f"{metabolite.id}_{phase.id}"
            )

            self.assertEqual(f"{metabolite.id}_{phase.id}", new_metabolite.id)
            self.assertEqual(metabolite.formula, new_metabolite.formula)
            self.assertEqual(metabolite.name, new_metabolite.name)
            self.assertEqual(metabolite.charge, new_metabolite.charge)
            self.assertEqual(
                metabolite.compartment, new_metabolite.compartment
            )
            self.assertEqual(metabolite.elements, new_metabolite.elements)
            self.assertEqual(
                metabolite.formula_weight, new_metabolite.formula_weight
            )

        for reaction in model.reactions:
            new_reaction: Reaction = new_model.reactions.get_by_id(
                f"{reaction.id}_{phase.id}"
            )

            self.assertEqual(f"{reaction.id}_{phase.id}", new_reaction.id)
            self.assertEqual(reaction.name, new_reaction.name)
            self.assertEqual(reaction.subsystem, new_reaction.subsystem)
            self.assertEqual(reaction.lower_bound, new_reaction.lower_bound)
            self.assertEqual(reaction.upper_bound, new_reaction.upper_bound)

            self.assertEqual(
                str(reaction.forward_variable).replace(
                    reaction.id, f"{reaction.id}_" f"{phase.id}"
                ),
                str(new_reaction.forward_variable),
            )

            objective_factor = phase.objective_factor * (
                phase.volume * phase.timeframe
            )

            self.assertEqual(
                reaction.objective_coefficient * objective_factor,
                new_reaction.objective_coefficient,
            )
            # ToDo compare metabolites

            # ToDo self.assertEqual(str(reaction.genes),str(new_reaction.genes)
            #  )
            self.assertMultiLineEqual(
                reaction.gene_reaction_rule, new_reaction.gene_reaction_rule
            )  # For some reason assertEqual does not Work
            self.assertEqual(
                reaction.gene_name_reaction_rule,
                new_reaction.gene_name_reaction_rule,
            )
            self.assertMultiLineEqual(
                repr(reaction.gpr), repr(new_reaction.gpr)
            )
            self.assertEqual(reaction.functional, new_reaction.functional)
            self.assertEqual(
                reaction.reversibility, new_reaction.reversibility
            )
            self.assertEqual(reaction.boundary, new_reaction.boundary)
            # ToDo self.assertEqual(reaction.reactants,new_reaction.reactants)
            #  Metabolite comparison

            # ToDo self.assertEqual(reaction.products,new_reaction.products)
            #  Metabolite comparison
            self.assertEqual(
                reaction.reaction,
                new_reaction.reaction.replace("_test_id", ""),
            )
            self.assertEqual(reaction.compartments, new_reaction.compartments)

        # Check the creation of objective functions
        model: Model = self.textbook.copy()
        phases = Phases()
        phases.add_phase(
            Phase(
                id="phase_1",
                light_dark="light",
                timeframe=2,
                volume=2,
            )
        )

        phases.add_phase(
            Phase(
                id="phase_2",
                light_dark="light",
                timeframe=1,
                volume=3,
            )
        )
        phases.add_phase(
            Phase(
                id="phase_3",
                light_dark="light",
                timeframe=1,
                volume=3,
                objective_factor=4.5,
            )
        )

        new_model = phases.apply_phases(model)

        objectives = str(
            sorted(
                linear_reaction_coefficients(new_model).items(),
                key=lambda x: x[0].id,
            )
        )
        self.assertRegex(
            objectives,
            r"\[\(<Reaction Biomass_Ecoli_core_phase_1 at .*>, 4\.0\), "
            r"\(<Reaction Biomass_Ecoli_core_phase_2 at .*>, 3\.0\), "
            r"\(<Reaction Biomass_Ecoli_core_phase_3 at .*>, 13\.5\)\]",
        )

    def test_to_xml(self):
        phases = Phases()
        phase = Phase(
            id="test_id",
            light_dark="light",
            timeframe=7,
            volume=3,
        )

        xml = phases.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "phases")

        self.assertEqual({}, xml.attrib)
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)

        phases.add_phase(phase)
        xml = phases.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "phases")

        self.assertEqual({}, xml.attrib)
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)
        self.assertEqual(len(list(xml)), 1)

        for child in xml:
            self.assertIsInstance(child, Element)
            self.assertEqual(child.tag, "phase")
            self.assertEqual(
                child.attrib,
                {
                    "id": "test_id",
                    "light_dark": "light",
                    "name": "",
                    "objective_factor": "1.0",
                    "timeframe": "7",
                    "volume": "3",
                },
            )
            self.assertIsNone(child.text)
            self.assertIsNone(child.tail)

    def test_from_dict(self):
        dict_list = [
            {
                "id": "leaf_0",
                "volume": 1,
                "name": "",
                "light_dark": "light",
                "timeframe": 2,
                "reaction": [
                    {"id": "ATPM", "lower_bound": 456, "upper_bound": 765}
                ],
            },
        ]
        phases = Phases.from_dict(dict_list)

        self.assertIsInstance(phases, Phases)
        self.assertEqual(len(phases.phases), 1)

        phase: Phase = phases.phases[0]

        self.assertEqual(phase.id, "leaf_0")
        self.assertEqual(phase.light_dark, "light")
        self.assertEqual(phase.timeframe, 2)
        self.assertEqual(phase.volume, 1)

        reaction = phase.reaction_settings[0]

        self.assertEqual("ATPM", reaction.id)
        self.assertEqual(456, reaction.lower_bound)
        self.assertEqual(765, reaction.upper_bound)

    def test_apply_phases_creates_a_group_per_phase(self):
        """Every phase must end up as a group in the extended model.

        The visualization relies on model.groups to select a phase, so a
        missing group silently removes that phase from the visualization.
        The first phase is the regression-prone one: it forms the base of
        the merged model and never passes through _merge.
        """

        model: Model = self.textbook.copy()
        phases = Phases()
        for phase_id in ("leaf_0", "root_0", "leaf_1"):
            phases.add_phase(Phase(id=phase_id, light_dark="light"))

        new_model = phases.apply_phases(model)

        self.assertEqual(
            {"leaf_0", "root_0", "leaf_1"},
            {group.id for group in new_model.groups},
        )

        for phase_id in ("leaf_0", "root_0", "leaf_1"):
            members = new_model.groups.get_by_id(phase_id).members

            self.assertEqual(
                len(model.reactions) + len(model.metabolites), len(members)
            )
            for member in members:
                self.assertTrue(member.id.endswith(f"_{phase_id}"))

    def test_manual_phase_gene_rules_are_preserved_and_warned(self):
        manual_a = self.textbook.copy()
        manual_b = self.textbook.copy()
        manual_a.reactions.get_by_id("PGI").gene_reaction_rule = (
            "manual_a_gene"
        )
        manual_b.reactions.get_by_id("PGI").gene_reaction_rule = (
            "manual_b_gene"
        )

        phases = Phases()
        for phase_id, model in (
            ("manual_a_0", manual_a),
            ("manual_b_0", manual_b),
        ):
            phase = Phase(id=phase_id, light_dark="light")
            phase.model = model
            phases.add_phase(phase)

        with self.assertWarns(GenesNotLinked) as context:
            result = phases.apply_phases(link_genes=True)

        # The warning has to name the phases it applies to, otherwise a
        # mixed setup gives no clue which rules were left alone.
        warning = context.warning
        self.assertEqual(["manual_a_0", "manual_b_0"], warning.phases)
        self.assertIn("manual_a_0, manual_b_0", str(warning))

        for phase_id, expected_rule in (
            ("manual_a_0", "manual_a_gene"),
            ("manual_b_0", "manual_b_gene"),
        ):
            reaction = result.reactions.get_by_id(f"PGI_{phase_id}")
            self.assertEqual(expected_rule, reaction.gene_reaction_rule)
            self.assertEqual(
                {expected_rule}, {gene.id for gene in reaction.genes}
            )
            self.assertIn(expected_rule, result.genes)

    def test_manual_phase_models_share_genes_with_identical_ids(self):
        """Same gene ID in two manual models: one Gene, two distinct rules."""
        manual_a = self.textbook.copy()
        manual_b = self.textbook.copy()
        manual_a.reactions.get_by_id("PGI").gene_reaction_rule = "shared_gene"
        manual_b.reactions.get_by_id("PGI").gene_reaction_rule = (
            "shared_gene and manual_b_gene"
        )

        phases = Phases()
        for phase_id, model in (
            ("manual_a_0", manual_a),
            ("manual_b_0", manual_b),
        ):
            phase = Phase(id=phase_id, light_dark="light")
            phase.model = model
            phases.add_phase(phase)

        with self.assertWarns(GenesNotLinked):
            result = phases.apply_phases(link_genes=True)

        reaction_a = result.reactions.get_by_id("PGI_manual_a_0")
        reaction_b = result.reactions.get_by_id("PGI_manual_b_0")

        # The rules stay phase specific, they are not synchronized.
        self.assertEqual("shared_gene", reaction_a.gene_reaction_rule)
        self.assertEqual(
            "shared_gene and manual_b_gene", reaction_b.gene_reaction_rule
        )

        # Gene IDs are not phase suffixed, so both reactions reference the
        # very same Gene, which now spans two phases.
        shared = result.genes.get_by_id("shared_gene")
        for reaction in (reaction_a, reaction_b):
            gene = next(
                gene for gene in reaction.genes if gene.id == "shared_gene"
            )
            self.assertIs(shared, gene)

        self.assertEqual(
            {"PGI_manual_a_0", "PGI_manual_b_0"},
            {reaction.id for reaction in shared.reactions},
        )
        self.assertEqual(
            {"manual_b_gene"},
            {gene.id for gene in reaction_b.genes} - {"shared_gene"},
        )
