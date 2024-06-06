import json
import dataclasses
import time
import random

import numpy as np
import deap.base
import deap.algorithms
import deap.tools

from . import types, defaults


class EvolutionRunner:
    def __init__(
        self,
        lib: type[types.FramsticksLibInterface],
        args: types.Args,
        toolbox_processor: types.ToolboxProcessor = lambda tb, *_: tb,
    ):
        lib.DETERMINISTIC = True
        random.seed(args.seed)
        np.random.seed(args.seed)
        self.frams_lib = lib(args.path, None, args.sim)
        toolbox = defaults.setup_toolbox(self.frams_lib, args)
        self.toolbox = toolbox_processor(toolbox, self.frams_lib, args)
        self.hof = deap.tools.HallOfFame(args.hof_size)
        self.args = args
        self.stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("stddev", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

    def run(self):
        pop = self.toolbox.population(n=self.args.popsize)
        time_start = time.perf_counter()
        pop, log = deap.algorithms.eaSimple(
            pop,
            self.toolbox,
            cxpb=self.args.pxov,
            mutpb=self.args.pmut,
            ngen=self.args.generations,
            stats=self.stats,
            halloffame=self.hof,
            verbose=True,
        )
        time_taken = time.perf_counter() - time_start

        print("Saving output to '%s'" % self.args.out)
        hof_instances = [
            {"genotype": ind[0], "fitness": ind.fitness.values} for ind in self.hof
        ]
        result = {
            "hof": hof_instances,
            "log": log,
            "args": dataclasses.asdict(self.args),
            "time_s": time_taken,
        }
        with open(self.args.out, "w") as outfile:
            json.dump(result, outfile)
        return
