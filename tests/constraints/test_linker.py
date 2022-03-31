from unittest import TestCase
from xml.etree.ElementTree import Element

from cobra import Model, Reaction
from cobra.test import create_test_model


from model_duplication.constraints.linker import Linker, Linkage
from model_duplication.constraints.phase import Phase, Phases


class TestLinker(TestCase):
    def test_create(self):
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        self.assertIsInstance(linker, Linker)

        self.assertEqual(linker.id, "test_id")
        self.assertEqual(linker.source, "source")
        self.assertEqual(linker.destination, "destination")

    def test_toString(self):
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        string = str(linker)
        expected = (
            "+---------+------+--------+-------------+--------------"
            "+--------------+\n"
            "|    ID   | Name | Source | Destination | Lower Bounds "
            "| Upper Bounds |\n"
            "+---------+------+--------+-------------+--------------"
            "+--------------+\n"
            "| test_id |      | source | destination |      0       "
            "|     1000     |\n"
            "+---------+------+--------+-------------+--------------"
            "+--------------+"
        )

        self.assertEqual(expected, string)

    def test_to_xml(self):
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        xml = linker.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "linker")
        self.assertEqual(
            xml.attrib,
            {"id": "test_id", "lower_bound": "0", "upper_bound": "1000"},
        )
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)

        self.assertEqual(len(list(xml)), 2)

        destination = xml.findall("destination")
        source = xml.findall("source")

        self.assertEqual(len(destination), 1)
        self.assertEqual(len(source), 1)

        destination = destination[0]
        source = source[0]

        self.assertIsInstance(destination, Element)
        self.assertEqual(destination.tag, "destination")
        self.assertEqual(destination.attrib, {"refid": "destination"})
        self.assertIsNone(destination.text)
        self.assertIsNone(destination.tail)

        self.assertIsInstance(source, Element)
        self.assertEqual(source.tag, "source")
        self.assertEqual(source.attrib, {"refid": "source"})
        self.assertIsNone(source.text)
        self.assertIsNone(source.tail)

    def test_from_dict(self):
        dic = {
            "id": "id",
            "lower_bound": "4",
            "upper_bound": "500",
            "destination": {"refid": "destination"},
            "source": {"refid": "source"},
        }

        linker = Linker.from_dict(dic)

        self.assertEqual(linker.id, "id")
        self.assertEqual(linker.lower_bound, 4)
        self.assertEqual(linker.upper_bound, 500)
        self.assertEqual(linker.destination, "destination")
        self.assertEqual(linker.source, "source")


class TestLinkage(TestCase):
    def test_create(self):
        linkage = Linkage()

        self.assertIsInstance(linkage, Linkage)
        self.assertEqual(linkage.linker, [])

    def test_toString(self):
        linkage = Linkage()

        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        linkage.add_linker(linker)

        string = str(linkage)
        expected = (
            "+---------+------+--------+-------------+--------------"
            "+--------------+\n"
            "|    ID   | Name | Source | Destination | Lower Bounds "
            "| Upper Bounds |\n"
            "+---------+------+--------+-------------+--------------"
            "+--------------+\n"
            "| test_id |      | source | destination |      0       "
            "|     1000     |\n"
            "+---------+------+--------+-------------+--------------"
            "+--------------+"
        )

        self.assertEqual(expected, string)

    def test_add_linker(self):
        linkage = Linkage()
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        linker2 = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        self.assertTrue(len(linkage.linker) == 0)
        linkage.add_linker(linker)

        self.assertTrue(len(linkage.linker) == 1)
        self.assertEqual(linkage.linker[0], linker)

        linkage.add_linker(linker2)

        expected = [linker, linker2]

        self.assertCountEqual(linkage.linker, expected)

    def test_remove_linker(self):
        linkage = Linkage()
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )

        linkage.add_linker(linker)

        self.assertEqual(len(linkage.linker), 1)
        linkage.remove_linker(linker)
        self.assertEqual(len(linkage.linker), 0)
        linkage.add_linker(linker)
        self.assertEqual(len(linkage.linker), 1)
        linkage.remove_linker(0)
        self.assertEqual(len(linkage.linker), 0)

    def test_apply_linkage(self):
        # ToDo use 2 Phases

        model: Model = create_test_model(model_name="textbook")

        linkage = Linkage()
        linker_default = Linker(
            id="gln__L_c",
            source="test_phase",
            destination="test_phase",
        )

        linker_non_default = Linker(
            id="nadp_c",
            source="test_phase",
            destination="test_phase",
            upper_bound=564,
            lower_bound=-1234,
        )

        linkage.add_linker(linker_default)
        linkage.add_linker(linker_non_default)
        phases = Phases()
        phases.add_phase(
            Phase(
                id="test_phase",
                light_dark="light",
                timeframe=3,
                volume=5,
            )
        )

        model = phases.apply_phases(model)
        model = linkage.apply_linkage(model, phases)

        linker_reaction = model.reactions.get_by_id(
            f"{linker_default.id}_L_{linker_default.source}"
            f"_{linker_default.destination}"
        )

        self.assertIsInstance(linker_reaction, Reaction)
        self.assertEqual(
            f"Linker for {linker_default.id} from {linker_default.source} "
            f"to {linker_default.destination}",
            linker_reaction.name,
        )
        self.assertEqual("Linker", linker_reaction.subsystem)
        self.assertEqual(0, linker_reaction.lower_bound)
        self.assertEqual(1000, linker_reaction.upper_bound)

        metabolites = linker_reaction.metabolites
        expected_metabolite = model.metabolites.get_by_id(
            "gln__L_c_test_phase"
        )

        self.assertEqual({expected_metabolite: 15}, metabolites)

        linker_reaction = model.reactions.get_by_id(
            f"{linker_non_default.id}_L_{linker_non_default.source}"
            f"_{linker_non_default.destination}"
        )

        self.assertIsInstance(linker_reaction, Reaction)
        self.assertEqual(
            f"Linker for {linker_non_default.id} from "
            f"{linker_non_default.source} to {linker_non_default.destination}",
            linker_reaction.name,
        )
        self.assertEqual("Linker", linker_reaction.subsystem)
        self.assertEqual(-1234, linker_reaction.lower_bound)
        self.assertEqual(564, linker_reaction.upper_bound)

        metabolites = linker_reaction.metabolites
        expected_metabolite = model.metabolites.get_by_id("nadp_c_test_phase")

        self.assertEqual({expected_metabolite: 15}, metabolites)

    def test_to_xml(self):
        linkage = Linkage()
        linker = Linker(
            id="test_id",
            source="source",
            destination="destination",
        )
        xml = linkage.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "linkage")

        self.assertEqual({}, xml.attrib)
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)

        linkage.add_linker(linker)
        xml = linkage.to_xml()

        self.assertIsInstance(xml, Element)
        self.assertEqual(xml.tag, "linkage")

        self.assertEqual({}, xml.attrib)
        self.assertIsNone(xml.text)
        self.assertIsNone(xml.tail)
        self.assertEqual(len(list(xml)), 1)

        for child in xml:
            self.assertIsInstance(child, Element)
            self.assertEqual(child.tag, "linker")
            self.assertEqual(
                child.attrib,
                {"id": "test_id", "lower_bound": "0", "upper_bound": "1000"},
            )
            self.assertIsNone(child.text)
            self.assertIsNone(child.tail)

    def test_from_dict(self):
        dict_list = [
            {
                "id": "id",
                "lower_bound": "4",
                "upper_bound": "500",
                "destination": {"refid": "destination"},
                "source": {"refid": "source"},
            }
        ]

        linkage = Linkage.from_dict(dict_list)

        self.assertIsInstance(linkage, Linkage)
        self.assertEqual(len(linkage.linker), 1)

        linker = linkage.linker[0]

        self.assertEqual(linker.id, "id")
        self.assertEqual(linker.lower_bound, 4)
        self.assertEqual(linker.upper_bound, 500)
        self.assertEqual(linker.destination, "destination")
        self.assertEqual(linker.source, "source")
