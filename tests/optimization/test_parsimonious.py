from unittest import TestCase

import cobra
from cobra import Configuration
from cobra.io import read_sbml_model
from importlib_resources import files, as_file

from cobra2d import Constraints
from cobra2d.optimization.parsimonious import (
    add_adjusted_pfba_objective,
)


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

        add_adjusted_pfba_objective(constraints=con, model=model)

        expected = (
            "4.0*12DGR120tipp_default_0 "
            "+ 4.0*12DGR120tipp_default_0_reverse_772b5 "
            "+ 4.0*12DGR120tipp_default_1 "
            "+ 4.0*12DGR120tipp_default_1_reverse_8c786 "
            "+ 4.0*12DGR120tipp_default_2 "
            "+ 4.0*12DGR120tipp_default_2_reverse_de4fd "
            "+ 4.0*12DGR140tipp_default_0 "
            "+ 4.0*12DGR140tipp_default_0_reverse_4cfd2 "
            "+ 4.0*12DGR140tipp_default_1 "
            "+ 4.0*12DGR140tipp_default_1_reverse_db595 "
            "+ 4.0*12DGR140tipp_default_2 "
            "+ 4.0*12DGR140tipp_default_2_reverse_2e5a9 "
            "+ 4.0*12DGR141tipp_default_0 "
            "+ 4.0*12DGR141tipp_default_0_reverse_e36a3 "
            "+ 4.0*12DGR141tipp_default_1 "
            "+ 4.0*12DGR141tipp_default_1_reverse_ab053 "
            "+ 4.0*12DGR141tipp_default_2 "
            "+ 4.0*12DGR141tipp_default_2_reverse_c5681 "
            "+ 4.0*12DGR160tipp_default_0 "
            "+ 4.0*12DGR160tipp_default_0_reverse_90889 "
            "+ 4.0*12DGR160tipp_default_1 "
            "+ 4.0*12DGR160tipp_default_1_reverse_ae3d3 "
            "+ 4.0*12DGR160tipp_default_2 "
            "+ 4.0*12DGR160tipp_default_2_reverse_cb384 "
            "+ 4.0*12DGR161tipp_default_0 "
            "+ 4.0*12DGR161tipp_default_0_reverse_f7abc "
            "+ 4.0*12DGR161tipp_default_1 "
            "+ 4.0*12DGR161tipp_default_1_reverse_"
        )

        self.assertEqual(expected, str(model.objective.expression)[:1000])
        # TestCase 2

        model = self.textbook.copy()
        con = Constraints()
        con.add_time_slots(3, 1, "light")
        con.add_time_slots(2, 4, "light")
        con.add_sub_models(["root", "leaf"], [1, 3])

        model = con.apply_to_model(model)

        add_adjusted_pfba_objective(constraints=con, model=model)
        expected = (
            "3.0*ACALD_leaf_0 + 3.0*ACALD_leaf_0_reverse_c7ccb "
            "+ 3.0*ACALD_leaf_1 + 3.0*ACALD_leaf_1_reverse_e6e28 "
            "+ 3.0*ACALD_leaf_2 + 3.0*ACALD_leaf_2_reverse_3a6c0 "
            "+ 12.0*ACALD_leaf_3 + 12.0*ACALD_leaf_3_reverse_84e0d "
            "+ 12.0*ACALD_leaf_4 + 12.0*ACALD_leaf_4_reverse_835f0 "
            "+ 1.0*ACALD_root_0 + 1.0*ACALD_root_0_reverse_a6976 "
            "+ 1.0*ACALD_root_1 + 1.0*ACALD_root_1_reverse_5eb64 "
            "+ 1.0*ACALD_root_2 + 1.0*ACALD_root_2_reverse_1b718 "
            "+ 4.0*ACALD_root_3 + 4.0*ACALD_root_3_reverse_0a0b8 "
            "+ 4.0*ACALD_root_4 + 4.0*ACALD_root_4_reverse_0dc3a "
            "+ 3.0*ACALDt_leaf_0 + 3.0*ACALDt_leaf_0_reverse_c6735 "
            "+ 3.0*ACALDt_leaf_1 + 3.0*ACALDt_leaf_1_reverse_517cf "
            "+ 3.0*ACALDt_leaf_2 + 3.0*ACALDt_leaf_2_reverse_63d61 "
            "+ 12.0*ACALDt_leaf_3 + 12.0*ACALDt_leaf_3_reverse_f4155 "
            "+ 12.0*ACALDt_leaf_4 + 12.0*ACALDt_leaf_4_reverse_314d1 "
            "+ 1.0*ACALDt_root_0 + 1.0*ACALDt_root_0_reverse_0d9ed "
            "+ 1.0*ACALDt_root_1 + 1.0*ACALDt_root_1_reverse_7df18 "
            "+ 1.0*ACALDt_root_2 + 1.0*ACALDt_root_2_reverse_eeb63 "
            "+ 4.0*ACALDt_root_3 + 4.0*ACALDt_root_3_re"
        )

        self.assertEqual(expected, str(model.objective.expression)[:1000])
        # TestCase 3 Linker

        model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(2, 2, "light")
        con.add_linker_series("12dgr140_c")
        model = con.apply_to_model(model=model)

        add_adjusted_pfba_objective(constraints=con, model=model)

        # Only the single linker reaction is excluded from the objective.
        self.assertEqual(10332, len(model.objective.variables))

    def test_adjusted_pfba(self):
        model = self.ecoli.copy()
        con = Constraints()
        con.add_time_slots(3, 4, "light")
        model = con.apply_to_model(model=model)
