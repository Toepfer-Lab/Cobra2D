from pprint import pprint
from unittest import TestCase

import cobra
from cobra import Configuration
from cobra.io import read_sbml_model
from cobra.util import linear_reaction_coefficients
from importlib_resources import files, as_file

from model_duplication import Constraints
from model_duplication.optimization.parsimonious import add_adjusted_pfba_objective


class TestParsimonious(TestCase):
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

    def test_add_adjusted_pfba_objective(self):
        model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(3, 4, "light")
        model = con.apply_to_model(model=model)

        add_adjusted_pfba_objective(constraints=con,
                                    model=model)

        expected = "4.0*12DGR120tipp_default-0 + 4.0*12DGR120tipp_default-0_reverse_18e2b + 4.0*12DGR120tipp_default-1 + 4.0*12DGR120tipp_default-1_reverse_88a03 + 4.0*12DGR120tipp_default-2 + 4.0*12DGR120tipp_default-2_reverse_42b88 + 4.0*12DGR140tipp_default-0 + 4.0*12DGR140tipp_default-0_reverse_3d8d8 + 4.0*12DGR140tipp_default-1 + 4.0*12DGR140tipp_default-1_reverse_b7da9 + 4.0*12DGR140tipp_default-2 + 4.0*12DGR140tipp_default-2_reverse_479fe + 4.0*12DGR141tipp_default-0 + 4.0*12DGR141tipp_default-0_reverse_a4a7e + 4.0*12DGR141tipp_default-1 + 4.0*12DGR141tipp_default-1_reverse_ae833 + 4.0*12DGR141tipp_default-2 + 4.0*12DGR141tipp_default-2_reverse_970f8 + 4.0*12DGR160tipp_default-0 + 4.0*12DGR160tipp_default-0_reverse_6f278 + 4.0*12DGR160tipp_default-1 + 4.0*12DGR160tipp_default-1_reverse_d5dc0 + 4.0*12DGR160tipp_default-2 + 4.0*12DGR160tipp_default-2_reverse_9fb9b + 4.0*12DGR161tipp_default-0 + 4.0*12DGR161tipp_default-0_reverse_81cff + 4.0*12DGR161tipp_default-1 + 4.0*12DGR161tipp_default-1_reverse_"
        self.assertEqual(expected, str(model.objective.expression)[:1000])
        # TestCase 2

        model = self.textbook.copy()
        con = Constraints()
        con.add_time_slots(3, 1, "light")
        con.add_time_slots(2, 4, "light")
        con.add_sub_models(["root", "leaf"], [1,3])

        model = con.apply_to_model(model)

        add_adjusted_pfba_objective(constraints=con,
                                    model=model)
        expected = "3.0*ACALD_leaf-0 + 3.0*ACALD_leaf-0_reverse_72443 + 3.0*ACALD_leaf-1 + 3.0*ACALD_leaf-1_reverse_da86c + 3.0*ACALD_leaf-2 + 3.0*ACALD_leaf-2_reverse_7a9cb + 12.0*ACALD_leaf-3 + 12.0*ACALD_leaf-3_reverse_daddf + 12.0*ACALD_leaf-4 + 12.0*ACALD_leaf-4_reverse_07b5d + 1.0*ACALD_root-0 + 1.0*ACALD_root-0_reverse_3e555 + 1.0*ACALD_root-1 + 1.0*ACALD_root-1_reverse_8c444 + 1.0*ACALD_root-2 + 1.0*ACALD_root-2_reverse_30749 + 4.0*ACALD_root-3 + 4.0*ACALD_root-3_reverse_2c4cf + 4.0*ACALD_root-4 + 4.0*ACALD_root-4_reverse_b0811 + 3.0*ACALDt_leaf-0 + 3.0*ACALDt_leaf-0_reverse_0f32d + 3.0*ACALDt_leaf-1 + 3.0*ACALDt_leaf-1_reverse_8f12e + 3.0*ACALDt_leaf-2 + 3.0*ACALDt_leaf-2_reverse_72061 + 12.0*ACALDt_leaf-3 + 12.0*ACALDt_leaf-3_reverse_dc5ef + 12.0*ACALDt_leaf-4 + 12.0*ACALDt_leaf-4_reverse_f1129 + 1.0*ACALDt_root-0 + 1.0*ACALDt_root-0_reverse_d4056 + 1.0*ACALDt_root-1 + 1.0*ACALDt_root-1_reverse_fd003 + 1.0*ACALDt_root-2 + 1.0*ACALDt_root-2_reverse_50e52 + 4.0*ACALDt_root-3 + 4.0*ACALDt_root-3_re"
        self.assertEqual(expected, str(model.objective.expression)[:1000])
        # TestCase 3 Linker

        model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(2, 2, "light")
        con.add_linker_series("12dgr140_c")
        model = con.apply_to_model(model=model)

        add_adjusted_pfba_objective(constraints=con,
                                    model=model)

        self.assertEqual(10316, len(model.objective.variables))


    def test_adjusted_pfba(self):
        model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(3, 4, "light")
        model = con.apply_to_model(model=model)

