import argparse
import deap.tools
import sys

import evolvengine.runner
import evolvengine.types

sys.path.append("..")

FramsticksLibCompetition = __import__("frams-gecco-2024.FramsticksLibCompetition")
# Use FramsticksLibCompetition instead of the default FramsticksLib
from FramsticksLibCompetition import FramsticksLibCompetition as FramsticksLib


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-path",
        required=True,
        help="Path to Framsticks library without trailing slash.",
    )
    parser.add_argument(
        "-sim",
        required=False,
        default="eval-allcriteria.sim",
        help='The name of the .sim file with settings for evaluation, mutation, crossover, and similarity estimation. If not given, "eval-allcriteria.sim" is assumed by default. Must be compatible with the "standard-eval" expdef. If you want to provide more files, separate them with a semicolon \';\'.',
    )

    parser.add_argument(
        "-genformat",
        required=False,
        default="1",
        help="Genetic format for the simplest initial genotype, for example 4, 9, or B. If not given, f1 is assumed.",
    )
    parser.add_argument(
        "-initialgenotype",
        required=False,
        help="The genotype used to seed the initial population. If given, the -genformat argument is ignored.",
    )

    parser.add_argument(
        "-opt",
        required=True,
        help="optimization criteria: vertpos, velocity, distance, vertvel, lifespan, numjoints, numparts, numneurons, numconnections (or other as long as it is provided by the .sim file and its .expdef). For multiple criteria optimization, separate the names by the comma.",
    )
    parser.add_argument(
        "-popsize", type=int, default=50, help="Population size, default: 50."
    )
    parser.add_argument(
        "-generations", type=int, default=5, help="Number of generations, default: 5."
    )
    parser.add_argument(
        "-tournament", type=int, default=5, help="Tournament size, default: 5."
    )
    parser.add_argument(
        "-pmut", type=float, default=0.9, help="Probability of mutation, default: 0.9"
    )
    parser.add_argument(
        "-pxov", type=float, default=0.2, help="Probability of crossover, default: 0.2"
    )
    parser.add_argument(
        "-hof_size",
        type=int,
        default=10,
        help="Number of genotypes in Hall of Fame. Default: 10.",
    )
    parser.add_argument(
        "-max_numparts",
        type=int,
        default=None,
        help="Maximum number of Parts. Default: no limit",
    )
    parser.add_argument(
        "-max_numjoints",
        type=int,
        default=None,
        help="Maximum number of Joints. Default: no limit",
    )
    parser.add_argument(
        "-max_numneurons",
        type=int,
        default=None,
        help="Maximum number of Neurons. Default: no limit",
    )
    parser.add_argument(
        "-max_numconnections",
        type=int,
        default=None,
        help="Maximum number of Neural connections. Default: no limit",
    )
    parser.add_argument(
        "-max_numgenochars",
        type=int,
        default=None,
        help="Maximum number of characters in genotype (including the format prefix, if any). Default: no limit",
    )
    parser.add_argument(
        "-seed",
        type=int,
        default=0,
        help="Seed for the random number generator. Default: 0",
    )
    parser.add_argument(
        "-out",
        required=False,
        help="If set, the Hall of Fame and log will be saved in this location. Must be .json",
    )
    return parser.parse_args()


def main():
    args = evolvengine.types.Args.from_args(parseArguments())
    runner = evolvengine.runner.EvolutionRunner(FramsticksLib, args)
    runner.run()


if __name__ == "__main__":
    main()
