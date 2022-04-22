import unittest
from xml.etree.ElementTree import Element

from cobra.core.model import Model
from cobra.core.reaction import Reaction
from cobra.test import create_test_model
from model_duplication.constraints.linker import Linkage, Linker
from model_duplication.constraints.phase import Phase, Phases

from model_duplication.constraints.transfer import Conveyance, Transfer
from model_duplication.error import NameWarning


class TestTransfer(unittest.TestCase):
    def test_create(self):
        transfer = Transfer(
            "identifier", Phase("root", "light"), Phase("stem", "light")
        )
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.id, "TR_identifier_root_stem")
        self.assertEqual(transfer.source, "root")
        self.assertEqual(transfer.destination, "stem")

        with self.assertWarnsRegex(
            NameWarning,
            "The use of strings is not recommended. Rather use a "
            "Phase to ensure an existing name",
        ):
            Transfer("identifier", "root", "stem")

    # TODO
    def test_toString(self):
        pass

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

    # TODO
    def test_from_dict(self):
        pass


class TestConveyance(unittest.TestCase):
    def test_create(self):
        conveyance = Conveyance()

        self.assertIsInstance(conveyance, Conveyance)
        self.assertEqual(conveyance, [])

    # TODO
    def test_toString(self):
        pass

    def test_dictlist_behavior(self):
        conveyance = Conveyance()
        transfer = Transfer(
            "metabolite",
            source=Phase("root", "light"),
            destination=Phase("stem", "light"),
        )

        conveyance.append(transfer)
        self.assertEqual(len(conveyance), 1)

        self.assertIsInstance(
            conveyance.get_by_id("TR_metabolite_root_stem"), Transfer
        )

        conveyance.remove(transfer)
        self.assertEqual(len(conveyance), 0)

    def test_apply(self):
        model: Model = create_test_model(model_name="textbook")

        # Regular Phases
        phases = Phases()
        phases.add_phase(
            Phase("root", "light"),
        )
        phases.add_phase(
            Phase("stem", "light", timeframe=5, volume=2),
        )

        test_model = phases.apply_phases(model, True)

        conveyance = Conveyance()
        transfer = Transfer(
            "gln__L_c",
            source=phases.phases.root,
            destination=phases.phases.stem,
        )

        conveyance.append(transfer)
        test_model = conveyance.apply(test_model, phases)

        reaction: Reaction = test_model.reactions.get_by_id(
            "TR_gln__L_c_root_stem"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root": -10, "gln__L_c_stem": 1},
        )

    def test_apply_complex(self):
        """Combination of linkers and transfers"""

        model: Model = create_test_model(model_name="textbook")

        # Should replicate behavior of add_sub_models and add_time_slots
        phases = Phases()
        phases.add_phase(
            Phase("root-0", "light"),
        )
        phases.add_phase(
            Phase("stem-0", "light"),
        )
        phases.add_phase(
            Phase("root-1", "light"),
        )
        phases.add_phase(
            Phase("stem-1", "light"),
        )
        model = phases.apply_phases(model, True)

        conveyance = Conveyance()
        linkage = Linkage()
        conveyance.append(
            Transfer(
                "gln__L_c",
                phases.phases.get_by_id("root-0"),
                phases.phases.get_by_id("stem-0"),
            )
        )
        conveyance.append(
            Transfer(
                "gln__L_c",
                phases.phases.get_by_id("root-1"),
                phases.phases.get_by_id("stem-1"),
            )
        )
        model = conveyance.apply(model, phases)

        linkage.add_linker(Linker("gln__L_c", "root-0", "root-1"))
        linkage.add_linker(Linker("gln__L_c", "stem-0", "stem-1"))
        model = linkage.apply_linkage(model, phases)

        reaction: Reaction = model.reactions.get_by_id(
            "TR_gln__L_c_root-0_stem-0"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root-0": -1, "gln__L_c_stem-0": 1},
        )

        reaction: Reaction = model.reactions.get_by_id(
            "TR_gln__L_c_root-1_stem-1"
        )
        self.assertDictEqual(
            {
                metabolite.id: value
                for metabolite, value in reaction.metabolites.items()
            },
            {"gln__L_c_root-1": -1, "gln__L_c_stem-1": 1},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)
