import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from xml.etree.ElementTree import Element

import cobra
from cobra import Model, Reaction, Configuration
from cobra.io import read_sbml_model
from graphviz import Digraph
from importlib_resources import files, as_file, open_text

from cobra2d.constraints.constraints import Constraints
from cobra2d.constraints.linker import Linkage, Linker
from cobra2d.constraints.phase import Phase, Phases
from cobra2d.error import PhaseNotFound
from tests import data


class TestConstraints(TestCase):
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

    def test_create(self):
        con = Constraints()

        self.assertIsInstance(con, Constraints)
        self.assertIsInstance(con.phases, Phases)
        self.assertIsInstance(con.linker, Linkage)

        self.assertEqual(1, len(con.phases.phases))
        default_phase: Phase = con.phases.phases[0]
        self.assertEqual("default_0", default_phase.id)
        self.assertEqual("Default Phase", default_phase.name)
        self.assertEqual("light", default_phase.light_dark)

    def test_toString(self):
        con = Constraints()
        string = str(con)
        expected = (
            "+----------------------+-----------+\n"
            "| Sub-Model\\Time Index |     0     |\n"
            "+----------------------+-----------+\n"
            "|           | id       | default_0 |\n"
            "|  default  | volume   |     1     |\n"
            "|           | time     |     1     |\n"
            "+----------------------+-----------+"
        )

        self.assertEqual(expected, string)

    def test_get_phase_by_id(self):
        con = Constraints()
        phase = con.get_phase_by_id("default_0")

        self.assertIsInstance(phase, Phase)
        self.assertEqual("default_0", phase.id)
        self.assertEqual("Default Phase", phase.name)
        self.assertEqual("light", phase.light_dark)

    def test_add_reaction_to_phase(self):
        con = Constraints()
        reaction = Reaction(
            id="test",
            lower_bound=4,
            upper_bound=541,
        )
        con.add_reaction_to_phase(reaction, "default_0")
        phase = con.get_phase_by_id("default_0")

        self.assertEqual(1, len(phase.reaction_settings))
        self.assertEqual("test", phase.reaction_settings[0].id)
        self.assertEqual(4, phase.reaction_settings[0].lower_bound)
        self.assertEqual(541, phase.reaction_settings[0].upper_bound)

    def test_add_time_slots(self):
        con = Constraints()
        con.add_time_slots(3, 4, "light")

        self.assertEqual(3, len(con.time_ranges))
        for index_expected, time_range in enumerate(con.time_ranges):
            index, time, light_dark = time_range
            self.assertEqual(index_expected, index)
            self.assertEqual(4, time)
            self.assertEqual("light", light_dark)

        self.assertEqual(3, len(con.phases.phases))
        for index, phase in enumerate(con.phases.phases):
            self.assertEqual(f"default_{index}", phase.id)
            self.assertEqual(1, phase.volume)
            self.assertEqual(4, phase.timeframe)

    def test_add_sub_models(self):
        con = Constraints()
        con.add_sub_models(["model0", "model1"], [0, 1], ["name", "name"])

        self.assertEqual(2, len(con.sub_models))

        for index, submodel in enumerate(con.sub_models):
            label, volume, name = submodel
            self.assertEqual(f"model{index}", label)
            self.assertEqual(index, volume)
            self.assertEqual("name", name)

        self.assertEqual(2, len(con.phases.phases))
        for index, phase in enumerate(con.phases.phases):
            self.assertEqual(f"model{index}_0", phase.id)
            self.assertEqual(index, phase.volume)
            self.assertEqual(1, phase.timeframe)
            self.assertEqual("light", phase.light_dark)

    def test_add_linker(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        linker = Linker(
            metabolite_id="test_id",
            source="default_0",
            destination="default_1",
        )

        self.assertEqual(0, len(con.linker.linker))
        con.add_linker(linker)
        self.assertEqual(1, len(con.linker.linker))
        self.assertEqual(linker, con.linker.linker[0])

        # Raise error if source or destination are not known

        linker = Linker(
            metabolite_id="test_id",
            source="unknown",
            destination="default_1",
        )

        with self.assertRaisesRegex(
            PhaseNotFound, "The source: 'unknown' is unknown."
        ):
            con.add_linker(linker)

        linker = Linker(
            metabolite_id="test_id",
            source="default_0",
            destination="unknown",
        )

        with self.assertRaisesRegex(
            PhaseNotFound, "The destination: 'unknown' is unknown."
        ):
            con.add_linker(linker)

    def test_add_linker_series(self):
        con = Constraints()
        con.add_time_slots(5, 1, "light")
        linker = []

        for n in range(4):
            source = f"default_{n}"
            destination = f"default_{n + 1}"
            linker.append(
                Linker(
                    metabolite_id="test_id",
                    source=source,
                    destination=destination,
                )
            )

        # last2first: bool = False reverse: bool = False
        self.assertEqual(0, len(con.linker.linker))
        con.add_linker_series("test_id")
        self.assertCountEqual(con.linker.linker, linker)

        # last2first: bool = True reverse: bool = False
        con = Constraints()
        con.add_time_slots(5, 1, "light")
        self.assertEqual(0, len(con.linker.linker))
        con.add_linker_series("test_id", last2first=True)

        linker.append(
            Linker(
                metabolite_id="test_id",
                source="default_4",
                destination="default_0",
            )
        )

        self.assertCountEqual(con.linker.linker, linker)

        # last2first: bool = False reverse: bool = True
        con = Constraints()
        con.add_time_slots(5, 1, "light")
        linker = []

        for n in range(4):
            destination = f"default_{n}"
            source = f"default_{n + 1}"
            linker.append(
                Linker(
                    metabolite_id="test_id",
                    source=source,
                    destination=destination,
                )
            )

        self.assertEqual(0, len(con.linker.linker))
        con.add_linker_series("test_id", reverse=True)
        self.assertCountEqual(linker, con.linker.linker)

        # last2first: bool = True reverse: bool = True
        linker.append(
            Linker(
                metabolite_id="test_id",
                source="default_0",
                destination="default_4",
            )
        )
        con = Constraints()
        con.add_time_slots(5, 1, "light")
        self.assertEqual(0, len(con.linker.linker))
        con.add_linker_series("test_id", last2first=True, reverse=True)
        self.assertCountEqual(linker, con.linker.linker)

        # phase is not usable
        con = Constraints()
        con.add_time_slots(4, 1, "light")
        con.add_sub_models(["root", "leaf"], [1, 2])
        self.assertEqual(0, len(con.linker.linker))
        del con.phases.phases[3]

        with self.assertRaisesRegex(
            PhaseNotFound, "The destination: 'root_3' is unknown."
        ):
            con.add_linker_series("test_linker")

    def test_apply_to_model(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        con.add_sub_models(["model0", "model1"], [1, 2], ["name", "name"])

        linker = Linker(
            metabolite_id="amp_c",
            source="model0_0",
            destination="model0_1",
        )
        con.add_linker(linker)

        model: Model = self.textbook.copy()
        new_model = con.apply_to_model(model)

        created_linker: Reaction = new_model.reactions.get_by_id(
            "amp_c_lk_model0_[0|1]"
        )

        self.assertEqual("amp_c_lk_model0_[0|1]", created_linker.id)
        self.assertEqual("amp_c_model0_0", created_linker.reactants[0].id)
        self.assertEqual("amp_c_model0_1", created_linker.products[0].id)
        self.assertEqual(0, created_linker.lower_bound)
        self.assertEqual(1000, created_linker.upper_bound)

        self.assertEqual(
            len(model.metabolites) * 4, len(new_model.metabolites)
        )
        self.assertEqual(
            len(model.reactions) * 4 + 1, len(new_model.reactions)
        )

        for label in con.sub_models:
            for time in con.time_ranges:
                for metabolite in model.metabolites:
                    new_id = f"{metabolite.id}_{label[0]}_{time[0]}"

                    try:
                        new_model.metabolites.get_by_id(new_id)
                    except KeyError:
                        self.fail(
                            f"No metabolite with ID {new_id} was found in the "
                            f"new model"
                        )

                for reaction in model.reactions:
                    new_id = f"{reaction.id}_{label[0]}_{time[0]}"

                    try:
                        new_model.reactions.get_by_id(new_id)
                    except KeyError:
                        self.fail(
                            f"No reaction with ID {new_id} was found in the"
                            f" new model"
                        )
        # test when Phase has a model

        con = Constraints()
        con.add_time_slots(2, 1, "light")
        phase = con.get_phase_by_id("default_0")
        phase_model: Model = self.textbook.copy()
        phase.model = phase_model
        model = self.textbook.copy()

        new_model = con.apply_to_model(model)
        self.assertEqual(
            len(phase_model.reactions) + len(model.reactions),
            len(new_model.reactions),
        )
        self.assertEqual(
            len(phase_model.metabolites) + len(model.metabolites),
            len(new_model.metabolites),
        )

        # simulation

        model: Model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(3, 1, "light")
        con.add_sub_models(["root", "leaf"], [2, 4])

        # check that base model results in expected summary
        with open_text(
            data, "ecoli_summary.txt", encoding="UTF-8"
        ) as expected:
            model.optimize()
            summary = str(model.summary())
            self.assertEqual(expected.read(), summary)

        textbook_model: Model = self.textbook.copy()

        with open_text(
            data, "textbook_summary.txt", encoding="UTF-8"
        ) as expected:
            textbook_model.optimize()
            summary = str(textbook_model.summary())
            self.assertEqual(expected.read(), summary)

        con.get_phase_by_id("leaf_1").model = textbook_model.copy()
        con.get_phase_by_id("root_2").model = textbook_model.copy()

        # no model given => Error
        with self.assertRaisesRegex(
            ValueError,
            "Model was None although there were phases without model.",
        ):
            con.apply_to_model()

        new_model = con.apply_to_model(model)
        solution = new_model.optimize()

        self.assertRegex(str(solution), r"^<Solution 17\.032.*>$")

        summary = str(new_model.summary())
        with open_text(data, "summary.txt", encoding="UTF-8") as expected:
            self.maxDiff = None
            self.assertEqual(expected.read(), summary)

    @unittest.skip("XML")
    def test_to_xml(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        con.add_sub_models(["model0", "model1"], [1, 2], ["name", "name"])

        linker = Linker(
            metabolite_id="amp_c",
            source="model0_0",
            destination="model0_1",
        )
        con.add_linker(linker)

        xml = con.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual("Conf", xml.tag)

        self.assertEqual(
            {
                "xmlns": "https://github.com/Toepfer-Lab/model_duplication/"
                "blob/main/src/resources/schema.xsd"
            },
            xml.attrib,
        )
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)

        # ToDo check children

    @unittest.skip("XML")
    def test_save_as_xml(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        con.add_sub_models(["model0", "model1"], [1, 2], ["name", "name"])

        linker = Linker(
            metabolite_id="amp_c",
            source="model0_0",
            destination="model0_1",
        )
        con.add_linker(linker)

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "out.xml"
            con.save_as_xml(path)

            with io.open(path) as save:
                with open_text(data, "out.xml", encoding="UTF-8") as expected:
                    self.assertListEqual(
                        list(expected),
                        list(save),
                    )

    @unittest.skip("XML")
    def test_load_from_xml(self):
        con_exp = Constraints()
        con_exp.add_time_slots(2, 1, "light")

        con_exp.add_sub_models(["model0", "model1"], [1, 2], ["name", "name"])

        linker = Linker(
            metabolite_id="amp_c",
            source="model0_0",
            destination="model0_1",
        )
        con_exp.add_linker(linker)
        con_exp.save_as_xml("out.xml")

        with open_text(data, "out.xml", encoding="UTF-8") as file:
            con_load = Constraints.load_from_xml(file)

        self.assertEqual(con_exp.default_time, con_load.default_time)
        self.assertEqual(con_exp.default_sub_model, con_load.default_sub_model)

        self.assertEqual(con_exp.time_ranges, con_load.time_ranges)
        self.assertEqual(con_exp.sub_models, con_load.sub_models)

        # compare phases
        # ToDo compare for Phase
        for phase in con_exp.phases.phases:
            try:
                load_phase: Phase = con_load.phases.phases.get_by_id(phase.id)
            except KeyError:
                self.fail(
                    f"No Phase with ID {phase.id} was found after loading"
                )

            self.assertEqual(phase.name, load_phase.name)
            self.assertEqual(phase.light_dark, load_phase.light_dark)
            self.assertEqual(phase.timeframe, load_phase.timeframe)
            self.assertEqual(phase.volume, load_phase.volume)
            # ToDo check reactions/testcase with reactions

        # compare linker
        self.assertCountEqual(con_exp.linker.linker, con_load.linker.linker)

    def test_create_graph(self):
        con_exp = Constraints()
        con_exp.add_time_slots(2, 1, "light")

        con_exp.add_sub_models(["model0", "model1"], [1, 2], ["name", "name"])

        linker = Linker(
            metabolite_id="amp_c",
            source="model0_0",
            destination="model0_1",
        )
        con_exp.add_linker(linker)

        g = con_exp.create_graph()
        self.assertIsInstance(g, Digraph)
        with open_text(
            data, "graphviz_Digraph_JSON.txt", encoding="UTF-8"
        ) as expected:
            self.assertEqual(str(g), expected.read())

    def test__constraint2networkx(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        con.add_sub_models(["leaf", "root"], [1, 2], ["leaf", "root"])

        linker = Linker(
            metabolite_id="amp_c",
            source="leaf_0",
            destination="leaf_1",
        )
        con.add_linker(linker)
        con.add_linker_series("atp_c", last2first=True)

        g = con._constraint2networkx()
        exp_edges = [
            (
                "leaf_0",
                "leaf_1",
                {"label": "atp_c", "Metabolite": "amp_c\natp_c"},
            ),
            ("leaf_1", "leaf_0", {"label": "atp_c", "Metabolite": "atp_c"}),
            ("root_0", "root_1", {"label": "atp_c", "Metabolite": "atp_c"}),
            ("root_1", "root_0", {"label": "atp_c", "Metabolite": "atp_c"}),
        ]

        exp_nodes = ["leaf_0", "leaf_1", "root_0", "root_1"]

        self.assertCountEqual(exp_edges, list(g.edges.data()))
        self.assertCountEqual(exp_nodes, g.nodes)

    def test__con2json(self):
        con = Constraints()
        con.add_time_slots(2, 1, "light")

        con.add_sub_models(["leaf", "root"], [1, 2], ["leaf", "root"])

        linker = Linker(
            metabolite_id="amp_c",
            source="leaf_0",
            destination="leaf_1",
        )
        con.add_linker(linker)
        con.add_linker_series("atp_c", last2first=True)

        print(con._con2json())

        (
            json_string,
            metabolites_existing_between_all_phases,
            metabolites_existing_between_all_phases_transfer,
        ) = con._con2json()

        with open_text(
            data, "con2json_result.JSON", encoding="UTF-8"
        ) as expected:
            self.assertEqual(json_string, json.load(expected))
