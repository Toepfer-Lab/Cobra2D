import logging
from typing import List, Union

from cobra import Metabolite, Model, Reaction
from prettytable import PrettyTable

from model_duplication.constraints.phase import Phase, Phases


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.level = 20


class Linker(Metabolite):
    source: Union[Phase, str]
    destination: Union[Phase, str]
    lower_bound: int
    upper_bound: int

    def __init__(self,
                 source: Phase,
                 destination: Phase,
                 lower_bound: int = 0,
                 upper_bound: int = 1000,
                 phases: Phases = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(source, str):
            try:
                source = phases.phases.get_by_id(source)
            except AttributeError:
                logger.error(
                    "When using id for phase identification, "
                    "the phases need to be passed as constructor variable."
                )
                raise KeyError("Missing phases Parameter")

        if isinstance(destination, str):
            try:
                destination = phases.phases.get_by_id(destination)
            except AttributeError:
                logger.error(
                    "When using id for phase identification, "
                    "the phases need to be passed as constructor variable."
                )
                raise KeyError("Missing phases Parameter")

        self.source = source
        self.destination = destination
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __str__(self):
        output = PrettyTable(["ID", "Name", "Source", "Destination", "Lower Bounds", "Upper Bounds"])

        return output.get_string()


class Linkage:
    linker: List[Linker]

    def __init__(self):
        self.linker = []

    def apply_linkage(self, model: Model):
        reactions2add: List[Reaction] = []

        for link in self.linker:
            source_metabolite: Metabolite = model.metabolites.get_by_id(link.id + "_" + link.source.id)
            destination_metabolite: Metabolite = model.metabolites.get_by_id(link.id + "_" + link.destination.id)

            linker: Reaction = Reaction(
                id=link.id + "_L_" + link.source.id + "_" + link.destination.id,
                name="Linker for " + link.id + " from " + link.source.id + " to " + link.destination.id,
                subsystem="Linker",
                lower_bound=link.lower_bound,
                upper_bound=link.upper_bound
            )

            linker.add_metabolites({
                source_metabolite: - link.destination.volume * link.destination.timeframe,
                destination_metabolite: link.source.volume * link.destination.timeframe
            })

            reactions2add.append(linker)

        model.add_reactions(reactions2add)

        return model
