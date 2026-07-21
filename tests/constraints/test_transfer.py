import unittest

from importlib_resources import files, as_file
from unittest import TestCase
from xml.etree.ElementTree import Element

import cobra
from cobra import Configuration
from cobra.core.model import Model
from cobra.core.reaction import Reaction
from cobra.io import read_sbml_model

from cobra2d.constraints.linker import Linkage, Linker
from cobra2d.constraints.phase import Phase, Phases

from cobra2d.constraints.transfer import Transfers, Transfer


class TestTransfer(TestCase):
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
        transfer = Transfer("identifier", "root", "stem")
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.metabolite_id, "identifier")
        self.assertEqual(transfer.source, "root")
        self.assertEqual(transfer.destination, "stem")

    def test_toString(self):
        transfer = Transfer(
            "identifier",
            Phase("root", "light"),
            Phase("stem", "light"),
            50,
            600,
        )
        self.assertEqual(
            str(transfer),
            (
                "+---------------+--------+-------------+--------------+--------------+\n"  # noqa: E501
                "| Metabolite ID | Source | Destination | Lower Bounds | Upper Bounds |\n"  # noqa: E501
                "+---------------+--------+-------------+--------------+--------------+\n"  # noqa: E501
                "|   identifier  |  root  |     stem    |      50      |     600      |\n"  # noqa: E501
                "+---------------+--------+-------------+--------------+--------------+"  # noqa: E501
            ),
        )

    def test_to_xml(self):
        transfer = Transfer(
            "identifier",
            Phase("root", "light"),
            Phase("stem", "light"),
            50,
            600,
        )
        xml = transfer.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "transfer")

        self.assertDictEqual(
            xml.attrib,
            {
                "metabolite": "identifier",
                "lower_bound": "50",
                "upper_bound": "600",
            },
        )

    def test_from_dict(self):
        dictionary = {
            "metabolite": "identifier",
            "lower_bound": "50",
            "upper_bound": "600",
            "destination": {"refid": "stem"},
            "source": {"refid": "root"},
        }
        transfer = Transfer.from_dict(dictionary)
        self.assertEqual(transfer.metabolite_id, "identifier")
        self.assertEqual(transfer.source, "root")
        self.assertEqual(transfer.destination, "stem")
        self.assertEqual(transfer.lower_bound, 50)
        self.assertEqual(transfer.upper_bound, 600)


class TestTransfers(TestCase):
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
        transfers = Transfers()

        self.assertIsInstance(transfers, Transfers)
        self.assertEqual(transfers.transfers, [])

    @unittest.skip("XML")
    def test_toString(self):
        transfers = Transfers()
        transfers.append(
            Transfer(
                "metabolite",
                source=Phase("root", "light"),
                destination=Phase("stem", "light"),
            )
        )
        transfers.append(
            Transfer(
                "metabolite",
                source=Phase("root2", "dark", 2),
                destination=Phase("stem2", "dark", 2),
            )
        )

        self.assertEqual(
            str(transfers),
            (
                "+---------------------------+---------------------------------------------+--------+-------------+--------------+--------------+\n"  # noqa: E501
                "|             ID            |                     Name                    | Source | Destination | Lower Bounds | Upper Bounds |\n"  # noqa: E501
                "+---------------------------+---------------------------------------------+--------+-------------+--------------+--------------+\n"  # noqa: E501
                "|  TR_metabolite_root_stem  |  Transfer for metabolite from root to stem  |  root  |     stem    |      0       |     1000     |\n"  # noqa: E501
                "| TR_metabolite_root2_stem2 | Transfer for metabolite from root2 to stem2 | root2  |    stem2    |      0       |     1000     |\n"  # noqa: E501
                "+---------------------------+---------------------------------------------+--------+-------------+--------------+--------------+"  # noqa: E501
            ),
        )

    @unittest.skip("XML")
    def test_from_dict(self):
        dictionary = [
            {
                "metabolite": "identifier",
                "lower_bound": "50",
                "upper_bound": "600",
                "destination": {"refid": "stem"},
                "source": {"refid": "root"},
            },
            {
                "metabolite": "identifier",
                "lower_bound": "0",
                "upper_bound": "1000",
                "destination": {"refid": "stem2"},
                "source": {"refid": "root2"},
            },
        ]
        transfers = Transfers.from_dict(dictionary)

        self.assertEqual(len(transfers), 2)
        self.assertEqual(
            transfers[1].metabolite_id, "TR_identifier_root2_stem2"
        )
        self.assertEqual(transfers[1].source, "root2")
        self.assertEqual(transfers[1].destination, "stem2")
        self.assertEqual(transfers[1].lower_bound, 0)
        self.assertEqual(transfers[1].upper_bound, 1000)

    def test_to_xml(self):
        transfers = Transfers()
        transfers.append(
            Transfer(
                "metabolite",
                source=Phase("root", "light"),
                destination=Phase("stem", "light"),
            )
        )

        transfers.append(
            Transfer(
                "metabolite",
                source=Phase("root2", "dark", 2),
                destination=Phase("stem2", "dark", 2),
            )
        )
        element = transfers.to_xml()

        for child in element:
            self.assertIsInstance(child, Element)
            self.assertEqual(child.tag, "transfer")
        self.assertEqual(
            element[1].attrib,
            {
                "metabolite": "metabolite",
                "lower_bound": "0",
                "upper_bound": "1000",
            },
        )
        self.assertEqual(
            element[0].attrib,
            {
                "metabolite": "metabolite",
                "lower_bound": "0",
                "upper_bound": "1000",
            },
        )

    def test_apply(self):
        model: Model = self.textbook.copy()

        # Regular Phases
        phases = Phases()
        phases.add_phase(
            Phase("root_0", "light"),
        )
        phases.add_phase(
            Phase("stem_0", "light", timeframe=5, volume=2),
        )

        test_model = phases.apply_phases(model, True)

        transfers = Transfers()
        transfer = Transfer(
            "gln__L_c",
            source=phases.phases.get_by_id("root_0"),
            destination=phases.phases.get_by_id("stem_0"),
        )

        transfers.append(transfer)
        test_model = transfers.apply(test_model, phases)

        reaction: Reaction = test_model.reactions.get_by_id(
            "gln__L_c_tr_[root|stem]_0"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root_0": -1, "gln__L_c_stem_0": 0.1},
        )

    def test_apply_complex(self):
        """Combination of linkers and transfers"""

        model: Model = self.textbook.copy()

        # Should replicate behavior of add_sub_models and add_time_slots
        phases = Phases()
        phases.add_phase(
            Phase("root_0", "light"),
        )
        phases.add_phase(
            Phase("stem_0", "light"),
        )
        phases.add_phase(
            Phase("root_1", "light"),
        )
        phases.add_phase(
            Phase("stem_1", "light"),
        )
        model = phases.apply_phases(model, True)

        transfers = Transfers()
        linkage = Linkage()
        transfers.append(
            Transfer(
                "gln__L_c",
                phases.phases.get_by_id("root_0"),
                phases.phases.get_by_id("stem_0"),
            )
        )
        transfers.append(
            Transfer(
                "gln__L_c",
                phases.phases.get_by_id("root_1"),
                phases.phases.get_by_id("stem_1"),
            )
        )
        model = transfers.apply(model, phases)

        linkage.add_linker(Linker("gln__L_c", "root_0", "root_1"))
        linkage.add_linker(Linker("gln__L_c", "stem_0", "stem_1"))
        model = linkage.apply_linkage(model, phases)

        reaction: Reaction = model.reactions.get_by_id(
            "gln__L_c_tr_[root|stem]_0"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root_0": -1, "gln__L_c_stem_0": 1},
        )

        reaction: Reaction = model.reactions.get_by_id(
            "gln__L_c_tr_[root|stem]_1"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root_1": -1, "gln__L_c_stem_1": 1},
        )
