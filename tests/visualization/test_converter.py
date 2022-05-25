import json
from importlib.resources import open_text
from pprint import pprint
from unittest import TestCase

import cobra
from cobra import Configuration
from cobra.io import read_sbml_model
from importlib_resources import files, as_file

from model_duplication.visualization import converter
from model_duplication.visualization.converter import cobra2igraph, cobra2networkx, cobra2metexplore, _group2lists
from tests import data


class TestConverter(TestCase):
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

    def test_cobra2igraph(self):
        model = self.textbook.copy()

        graph = cobra2igraph(model)
        with open_text(
                data, "textbook_igraph.txt", encoding="UTF-8"
        ) as expected:
            self.assertEqual(expected.read(), str(graph))


    def test_cobra2networkx(self):
        model = self.textbook.copy()

        graph = cobra2networkx(model)
        expected_nodes = ['13dpg_c', '2pg_c', '3pg_c', '6pgc_c', '6pgl_c', 'ac_c', 'ac_e', 'acald_c', 'acald_e', 'accoa_c', 'acon_C_c', 'actp_c', 'adp_c', 'akg_c', 'akg_e', 'amp_c', 'atp_c', 'cit_c', 'co2_c', 'co2_e', 'coa_c', 'dhap_c', 'e4p_c', 'etoh_c', 'etoh_e', 'f6p_c', 'fdp_c', 'for_c', 'for_e', 'fru_e', 'fum_c', 'fum_e', 'g3p_c', 'g6p_c', 'glc__D_e', 'gln__L_c', 'gln__L_e', 'glu__L_c', 'glu__L_e', 'glx_c', 'h2o_c', 'h2o_e', 'h_c', 'h_e', 'icit_c', 'lac__D_c', 'lac__D_e', 'mal__L_c', 'mal__L_e', 'nad_c', 'nadh_c', 'nadp_c', 'nadph_c', 'nh4_c', 'nh4_e', 'o2_c', 'o2_e', 'oaa_c', 'pep_c', 'pi_c', 'pi_e', 'pyr_c', 'pyr_e', 'q8_c', 'q8h2_c', 'r5p_c', 'ru5p__D_c', 's7p_c', 'succ_c', 'succ_e', 'succoa_c', 'xu5p__D_c', 'ACALD', 'ACALDt', 'ACKr', 'ACONTa', 'ACONTb', 'ACt2r', 'ADK1', 'AKGDH', 'AKGt2r', 'ALCD2x', 'ATPM', 'ATPS4r', 'Biomass_Ecoli_core', 'CO2t', 'CS', 'CYTBD', 'D_LACt2', 'ENO', 'ETOHt2r', 'EX_ac_e', 'EX_acald_e', 'EX_akg_e', 'EX_co2_e', 'EX_etoh_e', 'EX_for_e', 'EX_fru_e', 'EX_fum_e', 'EX_glc__D_e', 'EX_gln__L_e', 'EX_glu__L_e', 'EX_h_e', 'EX_h2o_e', 'EX_lac__D_e', 'EX_mal__L_e', 'EX_nh4_e', 'EX_o2_e', 'EX_pi_e', 'EX_pyr_e', 'EX_succ_e', 'FBA', 'FBP', 'FORt2', 'FORti', 'FRD7', 'FRUpts2', 'FUM', 'FUMt2_2', 'G6PDH2r', 'GAPD', 'GLCpts', 'GLNS', 'GLNabc', 'GLUDy', 'GLUN', 'GLUSy', 'GLUt2r', 'GND', 'H2Ot', 'ICDHyr', 'ICL', 'LDH_D', 'MALS', 'MALt2_2', 'MDH', 'ME1', 'ME2', 'NADH16', 'NADTRHD', 'NH4t', 'O2t', 'PDH', 'PFK', 'PFL', 'PGI', 'PGK', 'PGL', 'PGM', 'PIt2r', 'PPC', 'PPCK', 'PPS', 'PTAr', 'PYK', 'PYRt2', 'RPE', 'RPI', 'SUCCt2_2', 'SUCCt3', 'SUCDi', 'SUCOAS', 'TALA', 'THD2', 'TKT1', 'TKT2', 'TPI']
        expected_edges = [('2pg_c', 'ENO'), ('2pg_c', 'PGM'), ('3pg_c', 'Biomass_Ecoli_core'), ('3pg_c', 'PGK'), ('6pgc_c', 'GND'), ('6pgl_c', 'PGL'), ('ac_c', 'ACKr'), ('ac_e', 'ACt2r'), ('ac_e', 'EX_ac_e'), ('acald_c', 'ACALD'), ('acald_e', 'ACALDt'), ('acald_e', 'EX_acald_e'), ('accoa_c', 'Biomass_Ecoli_core'), ('accoa_c', 'CS'), ('accoa_c', 'MALS'), ('accoa_c', 'PTAr'), ('acon_C_c', 'ACONTb'), ('adp_c', 'ATPS4r'), ('adp_c', 'PYK'), ('akg_c', 'AKGDH'), ('akg_c', 'GLUSy'), ('akg_e', 'AKGt2r'), ('akg_e', 'EX_akg_e'), ('amp_c', 'ADK1'), ('atp_c', 'ACKr'), ('atp_c', 'ADK1'), ('atp_c', 'ATPM'), ('atp_c', 'Biomass_Ecoli_core'), ('atp_c', 'GLNS'), ('atp_c', 'GLNabc'), ('atp_c', 'PFK'), ('atp_c', 'PGK'), ('atp_c', 'PPCK'), ('atp_c', 'PPS'), ('atp_c', 'SUCOAS'), ('cit_c', 'ACONTa'), ('co2_c', 'PPC'), ('co2_e', 'CO2t'), ('co2_e', 'EX_co2_e'), ('coa_c', 'ACALD'), ('coa_c', 'AKGDH'), ('coa_c', 'PDH'), ('coa_c', 'PFL'), ('coa_c', 'SUCOAS'), ('dhap_c', 'TPI'), ('e4p_c', 'Biomass_Ecoli_core'), ('e4p_c', 'TKT2'), ('etoh_c', 'ALCD2x'), ('etoh_e', 'ETOHt2r'), ('etoh_e', 'EX_etoh_e'), ('f6p_c', 'Biomass_Ecoli_core'), ('f6p_c', 'PFK'), ('fdp_c', 'FBA'), ('fdp_c', 'FBP'), ('for_c', 'FORti'), ('for_e', 'EX_for_e'), ('for_e', 'FORt2'), ('fru_e', 'EX_fru_e'), ('fru_e', 'FRUpts2'), ('fum_c', 'FRD7'), ('fum_c', 'FUM'), ('fum_e', 'EX_fum_e'), ('fum_e', 'FUMt2_2'), ('g3p_c', 'Biomass_Ecoli_core'), ('g3p_c', 'GAPD'), ('g3p_c', 'TALA'), ('g6p_c', 'Biomass_Ecoli_core'), ('g6p_c', 'G6PDH2r'), ('g6p_c', 'PGI'), ('glc__D_e', 'EX_glc__D_e'), ('glc__D_e', 'GLCpts'), ('gln__L_c', 'Biomass_Ecoli_core'), ('gln__L_c', 'GLUN'), ('gln__L_c', 'GLUSy'), ('gln__L_e', 'EX_gln__L_e'), ('gln__L_e', 'GLNabc'), ('glu__L_c', 'Biomass_Ecoli_core'), ('glu__L_c', 'GLNS'), ('glu__L_c', 'GLUDy'), ('glu__L_e', 'EX_glu__L_e'), ('glu__L_e', 'GLUt2r'), ('glx_c', 'MALS'), ('h2o_c', 'ACONTb'), ('h2o_c', 'ATPM'), ('h2o_c', 'Biomass_Ecoli_core'), ('h2o_c', 'CS'), ('h2o_c', 'FBP'), ('h2o_c', 'FUM'), ('h2o_c', 'GLNabc'), ('h2o_c', 'GLUDy'), ('h2o_c', 'GLUN'), ('h2o_c', 'MALS'), ('h2o_c', 'PGL'), ('h2o_c', 'PPC'), ('h2o_c', 'PPS'), ('h2o_e', 'EX_h2o_e'), ('h2o_e', 'H2Ot'), ('h_c', 'CYTBD'), ('h_c', 'GLUSy'), ('h_c', 'NADH16'), ('h_c', 'PYK'), ('h_e', 'ACt2r'), ('h_e', 'AKGt2r'), ('h_e', 'ATPS4r'), ('h_e', 'D_LACt2'), ('h_e', 'ETOHt2r'), ('h_e', 'EX_h_e'), ('h_e', 'FORt2'), ('h_e', 'FUMt2_2'), ('h_e', 'GLUt2r'), ('h_e', 'MALt2_2'), ('h_e', 'PIt2r'), ('h_e', 'PYRt2'), ('h_e', 'SUCCt2_2'), ('h_e', 'SUCCt3'), ('h_e', 'THD2'), ('icit_c', 'ICDHyr'), ('icit_c', 'ICL'), ('lac__D_c', 'LDH_D'), ('lac__D_e', 'D_LACt2'), ('lac__D_e', 'EX_lac__D_e'), ('mal__L_c', 'MDH'), ('mal__L_c', 'ME1'), ('mal__L_c', 'ME2'), ('mal__L_e', 'EX_mal__L_e'), ('mal__L_e', 'MALt2_2'), ('nad_c', 'ACALD'), ('nad_c', 'AKGDH'), ('nad_c', 'ALCD2x'), ('nad_c', 'Biomass_Ecoli_core'), ('nad_c', 'GAPD'), ('nad_c', 'LDH_D'), ('nad_c', 'MDH'), ('nad_c', 'ME1'), ('nad_c', 'NADTRHD'), ('nad_c', 'PDH'), ('nadh_c', 'NADH16'), ('nadh_c', 'THD2'), ('nadp_c', 'G6PDH2r'), ('nadp_c', 'GLUDy'), ('nadp_c', 'GND'), ('nadp_c', 'ICDHyr'), ('nadp_c', 'ME2'), ('nadp_c', 'THD2'), ('nadph_c', 'Biomass_Ecoli_core'), ('nadph_c', 'GLUSy'), ('nadph_c', 'NADTRHD'), ('nh4_c', 'GLNS'), ('nh4_e', 'EX_nh4_e'), ('nh4_e', 'NH4t'), ('o2_c', 'CYTBD'), ('o2_e', 'EX_o2_e'), ('o2_e', 'O2t'), ('oaa_c', 'Biomass_Ecoli_core'), ('oaa_c', 'CS'), ('oaa_c', 'PPCK'), ('pep_c', 'Biomass_Ecoli_core'), ('pep_c', 'FRUpts2'), ('pep_c', 'GLCpts'), ('pep_c', 'PPC'), ('pep_c', 'PYK'), ('pi_c', 'ATPS4r'), ('pi_c', 'GAPD'), ('pi_c', 'PTAr'), ('pi_e', 'EX_pi_e'), ('pi_e', 'PIt2r'), ('pyr_c', 'Biomass_Ecoli_core'), ('pyr_c', 'PDH'), ('pyr_c', 'PFL'), ('pyr_c', 'PPS'), ('pyr_e', 'EX_pyr_e'), ('pyr_e', 'PYRt2'), ('q8_c', 'NADH16'), ('q8_c', 'SUCDi'), ('q8h2_c', 'CYTBD'), ('q8h2_c', 'FRD7'), ('r5p_c', 'Biomass_Ecoli_core'), ('r5p_c', 'RPI'), ('r5p_c', 'TKT1'), ('ru5p__D_c', 'RPE'), ('s7p_c', 'TALA'), ('succ_c', 'SUCCt3'), ('succ_c', 'SUCDi'), ('succ_c', 'SUCOAS'), ('succ_e', 'EX_succ_e'), ('succ_e', 'SUCCt2_2'), ('xu5p__D_c', 'TKT1'), ('xu5p__D_c', 'TKT2'), ('ACALD', 'accoa_c'), ('ACALD', 'h_c'), ('ACALD', 'nadh_c'), ('ACALDt', 'acald_c'), ('ACKr', 'actp_c'), ('ACKr', 'adp_c'), ('ACONTa', 'acon_C_c'), ('ACONTa', 'h2o_c'), ('ACONTb', 'icit_c'), ('ACt2r', 'ac_c'), ('ACt2r', 'h_c'), ('ADK1', 'adp_c'), ('AKGDH', 'co2_c'), ('AKGDH', 'nadh_c'), ('AKGDH', 'succoa_c'), ('AKGt2r', 'akg_c'), ('AKGt2r', 'h_c'), ('ALCD2x', 'acald_c'), ('ALCD2x', 'h_c'), ('ALCD2x', 'nadh_c'), ('ATPM', 'adp_c'), ('ATPM', 'h_c'), ('ATPM', 'pi_c'), ('ATPS4r', 'atp_c'), ('ATPS4r', 'h2o_c'), ('ATPS4r', 'h_c'), ('Biomass_Ecoli_core', 'adp_c'), ('Biomass_Ecoli_core', 'akg_c'), ('Biomass_Ecoli_core', 'coa_c'), ('Biomass_Ecoli_core', 'h_c'), ('Biomass_Ecoli_core', 'nadh_c'), ('Biomass_Ecoli_core', 'nadp_c'), ('Biomass_Ecoli_core', 'pi_c'), ('CO2t', 'co2_c'), ('CS', 'cit_c'), ('CS', 'coa_c'), ('CS', 'h_c'), ('CYTBD', 'h2o_c'), ('CYTBD', 'h_e'), ('CYTBD', 'q8_c'), ('D_LACt2', 'h_c'), ('D_LACt2', 'lac__D_c'), ('ENO', 'h2o_c'), ('ENO', 'pep_c'), ('ETOHt2r', 'etoh_c'), ('ETOHt2r', 'h_c'), ('FBA', 'dhap_c'), ('FBA', 'g3p_c'), ('FBP', 'f6p_c'), ('FBP', 'pi_c'), ('FORt2', 'for_c'), ('FORt2', 'h_c'), ('FORti', 'for_e'), ('FRD7', 'q8_c'), ('FRD7', 'succ_c'), ('FRUpts2', 'f6p_c'), ('FRUpts2', 'pyr_c'), ('FUM', 'mal__L_c'), ('FUMt2_2', 'fum_c'), ('FUMt2_2', 'h_c'), ('G6PDH2r', '6pgl_c'), ('G6PDH2r', 'h_c'), ('G6PDH2r', 'nadph_c'), ('GAPD', '13dpg_c'), ('GAPD', 'h_c'), ('GAPD', 'nadh_c'), ('GLCpts', 'g6p_c'), ('GLCpts', 'pyr_c'), ('GLNS', 'adp_c'), ('GLNS', 'gln__L_c'), ('GLNS', 'h_c'), ('GLNS', 'pi_c'), ('GLNabc', 'adp_c'), ('GLNabc', 'gln__L_c'), ('GLNabc', 'h_c'), ('GLNabc', 'pi_c'), ('GLUDy', 'akg_c'), ('GLUDy', 'h_c'), ('GLUDy', 'nadph_c'), ('GLUDy', 'nh4_c'), ('GLUN', 'glu__L_c'), ('GLUN', 'nh4_c'), ('GLUSy', 'glu__L_c'), ('GLUSy', 'nadp_c'), ('GLUt2r', 'glu__L_c'), ('GLUt2r', 'h_c'), ('GND', 'co2_c'), ('GND', 'nadph_c'), ('GND', 'ru5p__D_c'), ('H2Ot', 'h2o_c'), ('ICDHyr', 'akg_c'), ('ICDHyr', 'co2_c'), ('ICDHyr', 'nadph_c'), ('ICL', 'glx_c'), ('ICL', 'succ_c'), ('LDH_D', 'h_c'), ('LDH_D', 'nadh_c'), ('LDH_D', 'pyr_c'), ('MALS', 'coa_c'), ('MALS', 'h_c'), ('MALS', 'mal__L_c'), ('MALt2_2', 'h_c'), ('MALt2_2', 'mal__L_c'), ('MDH', 'h_c'), ('MDH', 'nadh_c'), ('MDH', 'oaa_c'), ('ME1', 'co2_c'), ('ME1', 'nadh_c'), ('ME1', 'pyr_c'), ('ME2', 'co2_c'), ('ME2', 'nadph_c'), ('ME2', 'pyr_c'), ('NADH16', 'h_e'), ('NADH16', 'nad_c'), ('NADH16', 'q8h2_c'), ('NADTRHD', 'nadh_c'), ('NADTRHD', 'nadp_c'), ('NH4t', 'nh4_c'), ('O2t', 'o2_c'), ('PDH', 'accoa_c'), ('PDH', 'co2_c'), ('PDH', 'nadh_c'), ('PFK', 'adp_c'), ('PFK', 'fdp_c'), ('PFK', 'h_c'), ('PFL', 'accoa_c'), ('PFL', 'for_c'), ('PGI', 'f6p_c'), ('PGK', '13dpg_c'), ('PGK', 'adp_c'), ('PGL', '6pgc_c'), ('PGL', 'h_c'), ('PGM', '3pg_c'), ('PIt2r', 'h_c'), ('PIt2r', 'pi_c'), ('PPC', 'h_c'), ('PPC', 'oaa_c'), ('PPC', 'pi_c'), ('PPCK', 'adp_c'), ('PPCK', 'co2_c'), ('PPCK', 'pep_c'), ('PPS', 'amp_c'), ('PPS', 'h_c'), ('PPS', 'pep_c'), ('PPS', 'pi_c'), ('PTAr', 'actp_c'), ('PTAr', 'coa_c'), ('PYK', 'atp_c'), ('PYK', 'pyr_c'), ('PYRt2', 'h_c'), ('PYRt2', 'pyr_c'), ('RPE', 'xu5p__D_c'), ('RPI', 'ru5p__D_c'), ('SUCCt2_2', 'h_c'), ('SUCCt2_2', 'succ_c'), ('SUCCt3', 'h_c'), ('SUCCt3', 'succ_e'), ('SUCDi', 'fum_c'), ('SUCDi', 'q8h2_c'), ('SUCOAS', 'adp_c'), ('SUCOAS', 'pi_c'), ('SUCOAS', 'succoa_c'), ('TALA', 'e4p_c'), ('TALA', 'f6p_c'), ('THD2', 'h_c'), ('THD2', 'nad_c'), ('THD2', 'nadph_c'), ('TKT1', 'g3p_c'), ('TKT1', 's7p_c'), ('TKT2', 'f6p_c'), ('TKT2', 'g3p_c'), ('TPI', 'g3p_c')]

        self.assertCountEqual(graph.nodes, expected_nodes)
        self.assertCountEqual(graph.edges, expected_edges)

    def test__group2lists(self):
        model = self.ecoli.copy()
        group = model.groups.get_by_id("g10")

        met_ids = ['no_c',
                   'no3_p',
                   'h_c',
                   'alltt_c',
                   'no2_p',
                   'alltn_c',
                   'no3_c',
                   'h2o_c',
                   'o2_c',
                   'q8h2_c',
                   'q8_c',
                   'nh4_p',
                   'hco3_c',
                   'peamn_p',
                   'glx_c',
                   'mqn8_c',
                   'mql8_c',
                   'pacald_p',
                   'n2o_c',
                   'urdglyc_c',
                   'cynt_c',
                   'co2_c',
                   'nadh_c',
                   '34dhpac_p',
                   'nad_c',
                   'tym_p',
                   'dopa_p',
                   'h2o2_p',
                   'h2o_p',
                   'h_p',
                   'nadph_c',
                   'nadp_c',
                   'o2_p',
                   '4hoxpacd_p',
                   'nh4_c']

        reac_ids = ['NO3R2bpp',
                    'NTRIR4pp',
                    '42A12BOOXpp',
                    'TYROXDApp',
                    'CYNTAH',
                    'PEAMNOpp',
                    'ALLTN',
                    'NTRIR3pp',
                    'NODOx',
                    'NODOy',
                    'NHFRBO',
                    'NO3R1bpp',
                    'UGLYCH']

        met, reac, gr = _group2lists(group)

        self.assertCountEqual(met_ids, [m.id for m in met])
        self.assertCountEqual(reac_ids, [r.id for r in reac])
        self.assertEqual(["g10"], [g.id for g in gr])

    # def test___create_and_append_links(self):

    def test_cobra2metexplore(self):
        model = self.textbook.copy()

        json_string = cobra2metexplore(model)

        with open_text(
                data, "textbook_metexplore.JSON", encoding="UTF-8"
        ) as expected:
            json_dict = json.loads(json_string)
            expected_dict = json.loads(expected.read())

        self.assertCountEqual(json_dict, expected_dict)

        # with remove parameter
        json_string = cobra2metexplore(model, removeUnselectedGroups= True)
        json_dict = json.loads(json_string)

        self.assertCountEqual(json_dict, expected_dict)

        with open_text(
                data, "ecoli_metexplore_g27.JSON", encoding="UTF-8"
        ) as expected:
            expected_dict = json.loads(expected.read())

        model = self.ecoli.copy()
        json_string = cobra2metexplore(model, removeUnselectedGroups= True, groups="g27")

        json_dict = json.loads(json_string)

        self.assertCountEqual(expected_dict, json_dict)

#    def test_cobra2metexplore_flux_file(self):

#    def test_cobra2metexplore_file(self):

#    def test_list2side_metabolite_file(self):

#    def test_metexplore(self):
