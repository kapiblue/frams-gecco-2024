import sys

import evolvengine.runner
import evolvengine.types
import evolvengine.algorithms
import evolvengine.defaults

sys.path.append("..")

FramsticksLibCompetition = __import__("frams-gecco-2024.FramsticksLibCompetition")
# Use FramsticksLibCompetition instead of the default FramsticksLib
from FramsticksLibCompetition import FramsticksLibCompetition as FramsticksLib
import frams


def main():
    args = evolvengine.types.RunConfig.from_args()
    toolbox = evolvengine.defaults.setup_toolbox(FramsticksLib, args)
    stats = evolvengine.defaults.setup_stats()
    stats.register("identity", lambda x: x)
    runner = evolvengine.runner.EvolutionRunner(FramsticksLib, args, toolbox, stats)
    print(frams.GenMan.f0_mut._value())
    runner.run()


if __name__ == "__main__":
    main()
