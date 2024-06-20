import math
import random
from . import types


class VaryingStrengthMutator:
    def __init__(
        self,
        mutate_func: types.Mutator,
        upper_bound: float = 5.0,
        lower_bound: float = 1.0,
        memory_length: int = 4,
        scale_factor: float = 0.1,
    ) -> None:
        self.max_fit_history = []
        self.strength = lower_bound
        self.mutate_func = mutate_func
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.memory_length = memory_length
        self.scale_factor = scale_factor

    def mutate(
        self, frame_lib: types.FramsticksLibInterface, individual: types.Individual
    ) -> tuple[types.Individual]:
        mutations_to_apply = self.strength
        individual = (individual,)
        while mutations_to_apply >= 1:
            individual = self.mutate_func(frame_lib, individual[0])
            mutations_to_apply -= 1
        if mutations_to_apply > 0:
            if random.random() < mutations_to_apply:
                individual = self.mutate_func(frame_lib, individual[0])
        return individual

    def update_strength(self, pop_fitnesses: list[tuple[float, float]]) -> float:
        max_fit = max(fit[0] for fit in pop_fitnesses)
        self.max_fit_history.append(max_fit)
        if len(self.max_fit_history) > self.memory_length:
            self.max_fit_history.pop(0)

        if (
            len(self.max_fit_history) < self.memory_length
            or self.max_fit_history[0] == 0
        ):
            return self.strength

        improvement_over_window = (
            self.max_fit_history[-1] - self.max_fit_history[0]
        ) / self.max_fit_history[0]
        if -0.01 < improvement_over_window < 0.01:
            self.strength = min(
                self.strength * (1 + self.scale_factor), self.upper_bound
            )
        else:
            self.strength = max(
                self.strength * (1 - self.scale_factor), self.lower_bound
            )
        return self.strength


class SimulatedAnnealingMutator:
    def __init__(
        self,
        mutate_func: types.Mutator,
        temperature: float = 100.0,
        cooling_rate: float = 0.01,
    ) -> None:
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.mutate_func = mutate_func
        self.previous_fitness = None

    def mutate(
        self, frame_lib: types.FramsticksLibInterface, individual: types.Individual
    ) -> tuple[types.Individual]:
        individual = (individual,)
        if self.temperature > random.randint(0, 100):
            individual = self.mutate_func(frame_lib, individual[0])
        return individual

    def update_temperature(self, pop_fitnesses: list[tuple[float, float]]) -> None:
        current_fitness = max(fit[0] for fit in pop_fitnesses)
        if (
            self.previous_fitness is not None
            and self.acceptance_probability(self.previous_fitness, current_fitness)
            <= random.random()
        ):
            self.temperature *= 1 - self.cooling_rate
        self.previous_fitness = current_fitness
        return self.temperature

    def acceptance_probability(
        self, previous_fitness: float, current_fitness: float
    ) -> float:
        if current_fitness > previous_fitness:
            return 1.0
        return math.exp((current_fitness - previous_fitness) / self.temperature)
