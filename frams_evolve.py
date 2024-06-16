import sys
import random

import numpy as np
import evolvengine.predefiner
import evolvengine.runner
import evolvengine.types
import evolvengine.algorithms
import evolvengine.defaults
import evolvengine.mutator
import evolvengine.randomizer

sys.path.append("..")

FramsticksLibCompetition = __import__("frams-gecco-2024.FramsticksLibCompetition")
# Use FramsticksLibCompetition instead of the default FramsticksLib
from FramsticksLibCompetition import FramsticksLibCompetition as FramsticksLib


def setup_lib(config: evolvengine.types.RunConfig) -> FramsticksLib:
    FramsticksLib.DETERMINISTIC = True
    random.seed(config.seed)
    np.random.seed(config.seed)
    return FramsticksLib(config.path, None, config.sim)


def main():
    config = evolvengine.types.RunConfig.from_args()
    lib = setup_lib(config)
    lib.TEST_FUNCTION = config.opt_func
    mutator = evolvengine.mutator.VaryingStrengthMutator(
        mutate_func=evolvengine.defaults.frams_mutate, upper_bound=config.mutator_ub
    )
    randomizer = evolvengine.randomizer.Randomizer(
        probability=config.rand_prob, lib=lib, iter_max=100
    )
    predefiner = evolvengine.predefiner.Predefiner(
        lib=lib,
        genformat=config.genformat,
        gen_path=config.predefined_file,
    )
    toolbox = evolvengine.defaults.setup_toolbox(lib, config)
    toolbox.register("population", predefiner.get_population)
    toolbox.register("mutate", lambda x: randomizer.randomize(mutator.mutate(lib, x)))
    stats = evolvengine.defaults.setup_stats()
    stats.register("m_strength", mutator.update_strength)
    runner = evolvengine.runner.EvolutionRunner(config, toolbox, stats)
    runner.run()


if __name__ == "__main__":
    main()
