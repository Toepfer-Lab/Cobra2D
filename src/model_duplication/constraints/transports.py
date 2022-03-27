from typing import List

from cobra import Reaction, Model, Metabolite

from model_duplication.constraints.phase import Phase


class LocalizedMetabolite(Metabolite):
    phase: Phase

    def __init__(self, phase: Phase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = phase


class Transport(Reaction):
    _metabolites: LocalizedMetabolite

    def __init__(self, source: Phase, destination: Phase, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add2Model(self, model: Model):
        metabolites: Metabolite = model.metabolites.get_by_id()


class Transports:
    transports: List[Transport]
