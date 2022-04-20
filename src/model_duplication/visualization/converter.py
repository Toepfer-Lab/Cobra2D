import networkx as nx
import igraph as ig
from cobra import Model, Metabolite, Reaction

from model_duplication.constraints import constraints


def cobra2igraph(model:Model):
    g = ig.Graph()

    metabolite:Metabolite
    for metabolite in model.metabolites:
        g.add_vertex(name= metabolite.id, color = "aliceblue")

    reaction: Reaction
    for reaction in model.reactions:
        g.add_vertex(name= reaction.id, color = "darkmagenta")
        for metabolite, coeff in reaction.metabolites.items():
            # direction
            if coeff > 0:
                g.add_edge(source= reaction.id, target= metabolite.id, coeff = coeff)
            else:
                g.add_edge(source= metabolite.id, target= reaction.id, coeff = coeff)

    return g


def cobra2networkx(model: Model):
    graph = nx.DiGraph()

    for metabolite in model.metabolites:
        graph.add_node(metabolite.id, type = "metabolite")

    for reaction in model.reactions:
        graph.add_node(reaction.id, type = "reaction")
        for metabolite, coeff in reaction.metabolites.items():
            if coeff >0:
                graph.add_edge(reaction.id, metabolite.id, coeff = coeff, type = "reaction")
            else:
                graph.add_edge(metabolite.id, reaction.id, coeff = -coeff, type = "reaction")

    return graph