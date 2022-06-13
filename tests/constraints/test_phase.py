from unittest import TestCase
from xml.etree.ElementTree import Element

import cobra
from cobra import DictList, Metabolite, Model, Reaction
from cobra.io import read_sbml_model
from importlib_resources import files, as_file

from model_duplication.constraints.phase import Phase, Phases


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
        phase = Phase(id="test_id", light_dark="light")

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
        }

        phase = Phase.from_dict(dic)

        self.assertEqual(phase.id, "test_id")
        self.assertEqual(phase.light_dark, "dark")
        self.assertEqual(phase.timeframe, 13)
        self.assertEqual(phase.volume, 7)
        # ToDo check Reactions


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
            self.assertEqual(
                reaction.objective_coefficient,
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
                    "timeframe": "7",
                    "volume": "3",
                },
            )
            self.assertIsNone(child.text)
            self.assertIsNone(child.tail)

    def test_from_dict(self):
        dict_list = [
            {
                "id": "leaf-0",
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

        self.assertEqual(phase.id, "leaf-0")
        self.assertEqual(phase.light_dark, "light")
        self.assertEqual(phase.timeframe, 2)
        self.assertEqual(phase.volume, 1)

        reaction = phase.reaction_settings[0]

        self.assertEqual("ATPM", reaction.id)
        self.assertEqual(456, reaction.lower_bound)
        self.assertEqual(765, reaction.upper_bound)
