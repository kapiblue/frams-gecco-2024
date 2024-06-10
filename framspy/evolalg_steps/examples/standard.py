import argparse
import os
import sys
import numpy as np

# TODO add new example: steadystate.py (analogous to standard.py) OR include steadysteate as a mode in this example or in niching_novelty.py
# TODO extend both standard.py and steadystate.py to support >1 criteria (using DEAP's selNSGA2() and selSPEA2())
# TODO add comments to all examples in this directory
# TODO add to standard.py and steadystate.py evaluating each genotype in HOF N (configurable, default 20) times when the evolution ends, as it is in niching_novelty.py
# TODO "-debug" mode, indent nested steps (pre++, post-- of a static counter?) and print their arguments so it is easy to see what happens during evolution


from FramsticksLib import FramsticksLib
from evolalg_steps.base.union_step import UnionStep
from evolalg_steps.experiment import Experiment
from evolalg_steps.fitness.fitness_step import FitnessStep
from evolalg_steps.mutation_cross.frams_cross_and_mutate import FramsCrossAndMutate
from evolalg_steps.population.frams_population import FramsPopulation
from evolalg_steps.repair.remove.field import FieldRemove
from evolalg_steps.selection.tournament import TournamentSelection
from evolalg_steps.statistics.halloffame_stats import HallOfFameStatistics
from evolalg_steps.statistics.statistics_deap import StatisticsDeap
from evolalg_steps.utils.population_save import PopulationSave



EVAL_LIFESPAN_BEHAVIOR = False  # if False, standard evaluation criteria can be used as fitness as defined by the -opt parameter. If True, it is assumed that the expdef provides custom dictionary fields in evaluation, and they need to be handled specifically in python source code below (this could be parametrized in command-line too, but the syntax would be complex).


def ensureDir(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Run this program with "python -u %s" if you want to disable buffering of its output.' % sys.argv[
            0])
    parser.add_argument('-path', type=ensureDir, required=True, help='Path to the Framsticks library without trailing slash.')
    parser.add_argument('-opt', required=True,
                        help='optimization criteria : vertpos, velocity, distance, vertvel, lifespan, numjoints, numparts, numneurons, numconnections (or other as long as it is provided by the .sim file and its .expdef). Single or multiple criteria.')
    parser.add_argument('-lib', required=False, help="Filename of .so or .dll with the Framsticks library")

    parser.add_argument('-genformat', required=False, default="1",
                        help='Genetic format for the demo run, for example 4, 9, or B. If not given, f1 is assumed.')
    parser.add_argument('-sim', required=False, default="eval-allcriteria.sim", help="Name of the .sim file with all parameter values. If you want to provide more files, separate them with a semicolon ';'.")
    parser.add_argument("-popsize", type=int, default=50, help="Population size, default 50.")
    parser.add_argument('-generations', type=int, default=5, help="Number of generations, default 5.")
    parser.add_argument('-tournament', type=int, default=5, help="Tournament size, default 5.")

    parser.add_argument('-hof_size', type=int, default=10, help="Number of genotypes in Hall of Fame. Default: 10.")
    return parser.parse_args()


def extract_fitness(ind):
    return ind.fitness


def print_population_count(pop):
    print("Current popsize:", len(pop))
    return pop  # Each step must return a population


def main():
    parsed_args = parseArguments()
    frams_lib = FramsticksLib(parsed_args.path, parsed_args.lib, parsed_args.sim)

    hall_of_fame = HallOfFameStatistics(parsed_args.hof_size, "fitness")
    statistics_union = UnionStep([
        hall_of_fame,
        StatisticsDeap([
            ("avg", np.mean),
            ("stddev", np.std),
            ("min", np.min),
            ("max", np.max),
            ("count", len)
        ], extract_fitness)
    ])

    fitness_remove = UnionStep(  # evaluate performance and fitness, rename some of the fields, and remove some performance fields that we get from Framsticks, but we don't need them here
        [
        FitnessStep(frams_lib, fields={"velocity": "fitness", "data->recording": "recording"},
                    fields_defaults={"velocity": None, "data->recording": None})  # custom definitions and handling
        if EVAL_LIFESPAN_BEHAVIOR else
        FitnessStep(frams_lib, fields={parsed_args.opt: "fitness"}, fields_defaults={parsed_args.opt: None})
        ]
        +
        ([FieldRemove("recording", None)] if EVAL_LIFESPAN_BEHAVIOR else [FieldRemove("fitness", None)])
        +
        [print_population_count]  # Stages can also be any Callable
    )

    selection = TournamentSelection(parsed_args.tournament, copy=True, fit_attr="fitness")
    new_generation_steps = [
        FramsCrossAndMutate(frams_lib, cross_prob=0.2, mutate_prob=0.9),
        fitness_remove
    ]

    generation_modifications = [
        statistics_union  # Or niching, novelty
    ]

    init_stages = [FramsPopulation(frams_lib, parsed_args.genformat, parsed_args.popsize),
                   fitness_remove,  # It is possible to create smaller population
                   statistics_union]

    end_steps = [PopulationSave("halloffame.gen", provider=hall_of_fame.halloffame,
                                fields={"genotype": "genotype", "fitness": "fitness", "custom": "recording"}
                                if EVAL_LIFESPAN_BEHAVIOR
                                else {"genotype": "genotype", "fitness": "fitness"}
                                )]

    experiment = Experiment(init_population=init_stages,
                            selection=selection,
                            new_generation_steps=new_generation_steps,
                            generation_modification=generation_modifications,
                            end_steps=end_steps,
                            population_size=parsed_args.popsize
                            )
    experiment.init()
    experiment.run(parsed_args.generations)
    for ind in hall_of_fame.halloffame:
        print("%g\t%s" % (ind.fitness, ind.genotype))


if __name__ == '__main__':
    main()
