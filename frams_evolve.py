import sys
import random

import numpy as np
import evolvengine.runner
import evolvengine.types
import evolvengine.algorithms
import evolvengine.defaults
import evolvengine.mutator

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
    mutator = evolvengine.mutator.VaryingStrengthMutator(
        mutate_func=evolvengine.defaults.frams_mutate, upper_bound=config.mutator_ub
    )
    toolbox = evolvengine.defaults.setup_toolbox(lib, config)
    toolbox.register("mutate", mutator.mutate, lib)
    stats = evolvengine.defaults.setup_stats()
    stats.register("m_strength", mutator.update_strength)
    runner = evolvengine.runner.EvolutionRunner(config, toolbox, stats)
    runner.run()


if __name__ == "__main__":
    main()
