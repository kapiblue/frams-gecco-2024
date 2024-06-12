import random

from .types import Individual, FramsticksLibInterface


class Randomizer:
    def __init__(
        self,
        probability: float,
        lib: FramsticksLibInterface,
        parts_min: int = 1,
        parts_max: int = 100,
        neurons_min: int = 1,
        neurons_max: int = 100,
        iter_max: int = 100,
    ) -> None:
        self.probability = probability
        self.lib = lib
        self.parts_min = parts_min
        self.parts_max = parts_max
        self.neurons_min = neurons_min
        self.neurons_max = neurons_max
        self.iter_max = iter_max

    def randomize(self, individual: Individual) -> Individual:
        if random.random() < self.probability:
            new_genotype = self.lib.getRandomGenotype(
                initial_genotype=individual[0][0],
                parts_min=self.parts_min,
                parts_max=self.parts_max,
                neurons_min=self.neurons_min,
                neurons_max=self.neurons_max,
                iter_max=self.iter_max,
                return_even_if_failed=True,
            )
            individual[0][0] = new_genotype
        return individual
