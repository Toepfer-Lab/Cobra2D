from typing import Literal, List
from cobra import Reaction, Model, DictList
from prettytable import PrettyTable

from model_duplication.duplication import _main_placeholder


class Phase:
    id: str
    name: str
    light_dark: Literal["light", "dark"]
    timeframe: int
    volume: int
    reaction_settings: List[Reaction]

    def __init__(self, id: str,
                 light_dark: Literal["light", "dark"],
                 timeframe: int = 1,
                 volume: int = 1,
                 name: str = ""):
        self.id = id
        self.volume = volume
        self.name = name
        self.light_dark = light_dark
        self.timeframe = timeframe


class Phases:
    phases: DictList[Phase]

    def __init__(self):
        self.phases = DictList()

    def __str__(self):
        output = PrettyTable(["Phase", "Name", "Volume", "Timeframe"])
        for phase in self.phases:
            output.add_row([
                phase.id,
                phase.name,
                phase.volume,
                phase.timeframe
            ])
        return output.get_string()

    def apply_phases(self, model: Model, link_genes: bool = False):
        phase_names = [phase.id for phase in self.phases]

        new_model = _main_placeholder(
            model=model,
            labels=phase_names,
            file=None,
            genes=link_genes
        )

        # ToDo change specified Reactions

        return new_model
