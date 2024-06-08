import sys

import evolvengine.runner
import evolvengine.types
import evolvengine.algorithms

sys.path.append("..")

FramsticksLibCompetition = __import__("frams-gecco-2024.FramsticksLibCompetition")
# Use FramsticksLibCompetition instead of the default FramsticksLib
from FramsticksLibCompetition import FramsticksLibCompetition as FramsticksLib


def main():
    args = evolvengine.types.RunConfig.from_args()
    runner = evolvengine.runner.EvolutionRunner(FramsticksLib, args)
    runner.run()


if __name__ == "__main__":
    main()
