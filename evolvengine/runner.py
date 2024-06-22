import json
import dataclasses
import time

import deap.base
import deap.algorithms
import deap.tools

from . import types, algorithms


class EvolutionRunner:
    def __init__(
        self,
        config: types.RunConfig,
        toolbox: deap.base.Toolbox,
        stats: deap.tools.Statistics,
    ):
        self.toolbox = toolbox
        self.hof = deap.tools.HallOfFame(config.hof_size)
        self.config = config
        self.stats = stats

    def run(self) -> None:
        pop = self.toolbox.population(n=self.config.popsize)
        time_start = time.perf_counter()
        algorithm = algorithms.resolve_algorithm(self.config)
        # Workaround for DPGA periodical saving
        if algorithm.__name__ == "dpga":
            pop, log = algorithm(
                pop,
                self.toolbox,
                cxpb=self.config.pxov,
                mutpb=self.config.pmut,
                ngen=self.config.generations,
                stats=self.stats,
                halloffame=self.hof,
                verbose=True,
                config=self.config,
                save_period=5,  # save every 5 generations
            )
        else:
            pop, log = algorithm(
                pop,
                self.toolbox,
                cxpb=self.config.pxov,
                mutpb=self.config.pmut,
                ngen=self.config.generations,
                stats=self.stats,
                halloffame=self.hof,
                verbose=True,
            )
        time_taken = time.perf_counter() - time_start

        print("Saving output to '%s'" % self.config.out)
        hof_instances = [
            {"genotype": ind[0], "fitness": ind.fitness.values} for ind in self.hof
        ]
        result = {
            "hof": hof_instances,
            "log": log,
            "args": dataclasses.asdict(self.config),
            "time_s": time_taken,
        }
        with open(self.config.out, "w") as outfile:
            json.dump(result, outfile, default=str)
