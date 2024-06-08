import json
import dataclasses
import time
import random

import numpy as np
import deap.base
import deap.algorithms
import deap.tools

from . import types, defaults, algorithms


class EvolutionRunner:
    def __init__(
        self,
        lib: type[types.FramsticksLibInterface],
        config: types.RunConfig,
        toolbox_processor: types.ToolboxProcessor = lambda tb, *_: tb,
    ):
        lib.DETERMINISTIC = True
        random.seed(config.seed)
        np.random.seed(config.seed)
        self.frams_lib = lib(config.path, None, config.sim)
        toolbox = defaults.setup_toolbox(self.frams_lib, config)
        self.toolbox = toolbox_processor(toolbox, self.frams_lib, config)
        self.hof = deap.tools.HallOfFame(config.hof_size)
        self.config = config
        self.stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("stddev", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

    def run(self):
        pop = self.toolbox.population(n=self.config.popsize)
        time_start = time.perf_counter()
        algorithm = algorithms.resolve_algorithm(self.config)
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
            json.dump(result, outfile)
