import argparse
import os
import sys
import numpy as np
import pandas as pd
from deap import creator, base, tools, algorithms
from FramsticksLib import FramsticksLib

import pickle
from time import time
import frams

# Note: this may be less efficient than running the evolution directly in Framsticks
# so if performance is key, compare both options.


def genotype_within_constraint(
    genotype, dict_criteria_values, criterion_name, constraint_value
):
    REPORT_CONSTRAINT_VIOLATIONS = False
    if constraint_value is not None:
        actual_value = dict_criteria_values[criterion_name]
        if actual_value > constraint_value:
            if REPORT_CONSTRAINT_VIOLATIONS:
                print(
                    'Genotype "%s" assigned low fitness because it violates constraint "%s": %s exceeds threshold %s'
                    % (genotype, criterion_name, actual_value, constraint_value)
                )
            return False
    return True


def frams_evaluate(frams_lib, individual):
    BAD_FITNESS = [-1] * len(
        OPTIMIZATION_CRITERIA
    )  # fitness of -1 is intended to discourage further propagation of this genotype via selection ("this genotype is very poor")
    genotype = individual[
        0
    ]  # individual[0] because we can't (?) have a simple str as a deap genotype/individual, only list of str.
    data = frams_lib.evaluate([genotype])
    # print("Evaluated '%s'" % genotype, 'evaluation is:', data)
    valid = True
    try:
        first_genotype_data = data[0]
        evaluation_data = first_genotype_data["evaluations"]
        default_evaluation_data = evaluation_data[""]
        fitness = [default_evaluation_data[crit] for crit in OPTIMIZATION_CRITERIA]
    except (
        KeyError,
        TypeError,
    ) as e:  # the evaluation may have failed for an invalid genotype (such as X[@][@] with "Don't simulate genotypes with warnings" option), or because the creature failed to stabilize, or for some other reason
        valid = False
        print(
            'Problem "%s" so could not evaluate genotype "%s", hence assigned it low fitness: %s'
            % (str(e), genotype, BAD_FITNESS)
        )
    if valid:
        default_evaluation_data["numgenocharacters"] = len(
            genotype
        )  # for consistent constraint checking below
        valid &= genotype_within_constraint(
            genotype, default_evaluation_data, "numparts", parsed_args.max_numparts
        )
        valid &= genotype_within_constraint(
            genotype, default_evaluation_data, "numjoints", parsed_args.max_numjoints
        )
        valid &= genotype_within_constraint(
            genotype, default_evaluation_data, "numneurons", parsed_args.max_numneurons
        )
        valid &= genotype_within_constraint(
            genotype,
            default_evaluation_data,
            "numconnections",
            parsed_args.max_numconnections,
        )
        valid &= genotype_within_constraint(
            genotype,
            default_evaluation_data,
            "numgenocharacters",
            parsed_args.max_numgenochars,
        )
        if fitness[0] < 0:
            num_parts = default_evaluation_data["numparts"]
            num_joints = default_evaluation_data["numjoints"]
            fitness = 1 / (1 + np.exp(-num_parts * (num_joints+1)))
            fitness = [fitness / 10] * len(OPTIMIZATION_CRITERIA)
    if not valid:
        fitness = BAD_FITNESS
    return fitness


def frams_crossover(frams_lib, individual1, individual2):
    geno1 = individual1[
        0
    ]  # individual[0] because we can't (?) have a simple str as a deap genotype/individual, only list of str.
    geno2 = individual2[
        0
    ]  # individual[0] because we can't (?) have a simple str as a deap genotype/individual, only list of str.
    individual1[0] = frams_lib.crossOver(geno1, geno2)
    individual2[0] = frams_lib.crossOver(geno1, geno2)
    return individual1, individual2


def frams_mutate(frams_lib, individual):
    individual[0] = frams_lib.mutate([individual[0]])[
        0
    ]  # individual[0] because we can't (?) have a simple str as a deap genotype/individual, only list of str.
    return (individual,)


def frams_getsimplest(frams_lib, genetic_format, initial_genotype):
    return (
        initial_genotype
        if initial_genotype is not None
        else frams_lib.getSimplest(genetic_format)
    )


def prepareToolbox(
    frams_lib, OPTIMIZATION_CRITERIA, tournament_size, genetic_format, initial_genotype
):
    creator.create(
        "FitnessMax", base.Fitness, weights=[1.0] * len(OPTIMIZATION_CRITERIA)
    )
    creator.create(
        "Individual", list, fitness=creator.FitnessMax
    )  # would be nice to have "str" instead of unnecessary "list of str"

    toolbox = base.Toolbox()
    toolbox.register(
        "attr_simplest_genotype",
        frams_getsimplest,
        frams_lib,
        genetic_format,
        initial_genotype,
    )  # "Attribute generator"
    # (failed) struggle to have an individual which is a simple str, not a list of str
    # toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_frams)
    # https://stackoverflow.com/questions/51451815/python-deap-library-using-random-words-as-individuals
    # https://github.com/DEAP/deap/issues/339
    # https://gitlab.com/santiagoandre/deap-customize-population-example/-/blob/master/AGbasic.py
    # https://groups.google.com/forum/#!topic/deap-users/22g1kyrpKy8
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.Individual,
        toolbox.attr_simplest_genotype,
        1,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", frams_evaluate, frams_lib)
    toolbox.register("mate", frams_crossover, frams_lib)
    toolbox.register("mutate", frams_mutate, frams_lib)
    if len(OPTIMIZATION_CRITERIA) <= 1:
        toolbox.register("select", tools.selTournament, tournsize=tournament_size)
    else:
        toolbox.register("select", tools.selNSGA2)
    return toolbox


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Run this program with "python -u %s" if you want to disable buffering of its output.'
        % sys.argv[0]
    )
    parser.add_argument(
        "-path",
        type=ensureDir,
        required=True,
        help="Path to Framsticks library without trailing slash.",
    )
    parser.add_argument(
        "-lib",
        required=False,
        help='Library name. If not given, "frams-objects.dll" (or .so or .dylib) is assumed depending on the platform.',
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
        "-hof_savefile",
        required=False,
        help="If set, Hall of Fame will be saved in Framsticks file format (recommended extension *.gen).",
    )
    parser.add_argument(
        "-log_savefile",
        required=False,
        help="If set, the log will be saved in this location. Must be .pkl",
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
        "-run_id",
        type=int,
        default=0,
        help="Evolutionary run id. Default: 0",
    )
    return parser.parse_args()


def ensureDir(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def save_genotypes(filename, OPTIMIZATION_CRITERIA, hof):
    from framsfiles import writer as framswriter

    with open(filename, "w") as outfile:
        for ind in hof:
            keyval = {}
            for i, k in enumerate(
                OPTIMIZATION_CRITERIA
            ):  # construct a dictionary with criteria names and their values
                keyval[k] = ind.fitness.values[
                    i
                ]  # TODO it would be better to save in Individual (after evaluation) all fields returned by Framsticks, and get these fields here, not just the criteria that were actually used as fitness in evolution.
            # Note: prior to the release of Framsticks 5.0, saving e.g. numparts (i.e. P) without J,N,C breaks re-calcucation of P,J,N,C in Framsticks and they appear to be zero (nothing serious).
            outfile.write(
                framswriter.from_collection(
                    {"_classname": "org", "genotype": ind[0], **keyval}
                )
            )
            outfile.write("\n")
    print("Saved '%s' (%d)" % (filename, len(hof)))


def update_f1_probab(nevals: int, max_neavals: int) -> None:
    ratio = nevals / max_neavals
    print("Ratio: ", ratio)
    # frams.GenMan.f1_smX = 0.5 * np.maximum(1 - (ratio), 0.3)
    # frams.GenMan.f1_smJunct = 0.3 * np.maximum(1 - (ratio), 0.4)
    # frams.GenMan.f1_smComma = 0.1 * np.maximum(1 - (ratio), 0.6)
    # frams.GenMan.f1_smModif = 0.8 * np.maximum(1 - (ratio**2), 0.7)
    # frams.GenMan.f1_nmNeu = 0.3 * np.minimum(ratio, 0.9)
    # frams.GenMan.f1_nmConn = 0.4 * np.minimum(ratio, 0.5)
    # frams.GenMan.f1_nmProp = np.minimum(ratio, 0.3)
    # frams.GenMan.f1_nmWei = 1.2 * np.minimum(ratio, 0.9)
    # frams.GenMan.f1_nmVal = 0.6 * np.minimum(ratio, 0.7)

    # frams.GenMan.f1_smX = 0.7 * np.minimum(ratio, 0.9)
    # frams.GenMan.f1_smJunct = 0.7 * np.minimum(ratio, 0.7)
    # frams.GenMan.f1_smComma = np.minimum(ratio, 0.5)
    # frams.GenMan.f1_smModif = 2 * np.minimum(ratio, 0.9)
    # frams.GenMan.f1_nmNeu = 0.2 * np.maximum(1 - (ratio), 0.3)
    # frams.GenMan.f1_nmConn = 0.5 * np.maximum(1 - (ratio), 0.5)
    # frams.GenMan.f1_nmProp = 0.2 * np.maximum(1 - (ratio), 0.6)
    # frams.GenMan.f1_nmWei = 0.8 * np.maximum(1 - (ratio**2), 0.8)
    # frams.GenMan.f1_nmVal = 0.3 * np.maximum(1 - (ratio), 0.9)

    frams.GenMan.f1_smModif = 1.02 * float(str(frams.GenMan.f1_smModif))
    frams.GenMan.f1_smX = 1.01 * float(str(frams.GenMan.f1_smX))
    frams.GenMan.f1_nmNeu = 1.03 * float(str(frams.GenMan.f1_nmNeu))
    frams.GenMan.f1_nmConn = 1.01 * float(str(frams.GenMan.f1_nmConn))

    print("frams.GenMan.f1_smX:", frams.GenMan.f1_smX,
          "\nframs.GenMan.f1_smJunct:", frams.GenMan.f1_smJunct,
          "\nframs.GenMan.f1_smComma:", frams.GenMan.f1_smComma,
          "\nframs.GenMan.f1_smModif:", frams.GenMan.f1_smModif,
          "\nframs.GenMan.f1_nmNeu:", frams.GenMan.f1_nmNeu,
          "\nframs.GenMan.f1_nmConn:", frams.GenMan.f1_nmConn,
          "\nframs.GenMan.f1_nmProp:", frams.GenMan.f1_nmProp,
          "\nframs.GenMan.f1_nmWei:", frams.GenMan.f1_nmWei,
          "\nframs.GenMan.f1_nmVal:", frams.GenMan.f1_nmVal)


def eaSimple_mut(population, toolbox, cxpb, mutpb, ngen, stats=None,
                 halloffame=None, verbose=__debug__,
                 hof_savefile=None):
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Cumulative nevals
    # total_nevals = 0
    # max_nevals = len(population) * ngen
    
    current_hof_solutions = None

    # Begin the generational process
    for gen in range(1, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)
            # Save the hof solutions to file
            if current_hof_solutions != halloffame[0]:
                current_hof_solutions = halloffame[0]
                filename = hof_savefile[:-4] + f'-g-{gen}.gen'
                save_genotypes(filename, OPTIMIZATION_CRITERIA, halloffame)
                print("New best solution found:", current_hof_solutions)

        # Replace the current population by the offspring
        population[:] = offspring

        # total_nevals += len(invalid_ind)
        # if gen % 10 == 0:
        #     update_f1_probab(nevals=total_nevals, max_neavals=max_nevals)

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

    return population, logbook


def main():
    global parsed_args, OPTIMIZATION_CRITERIA  # needed in frams_evaluate(), so made global to avoid passing as arguments

    # random.seed(123)  # see FramsticksLib.DETERMINISTIC below, set to True if you want full determinism
    FramsticksLib.DETERMINISTIC = (
        False  # must be set before FramsticksLib() constructor call
    )
    parsed_args = parseArguments()
    print(
        "Argument values:",
        ", ".join(
            ["%s=%s" % (arg, getattr(parsed_args, arg)) for arg in vars(parsed_args)]
        ),
    )
    OPTIMIZATION_CRITERIA = parsed_args.opt.split(",")
    framsLib = FramsticksLib(parsed_args.path, parsed_args.lib, parsed_args.sim)
    toolbox = prepareToolbox(
        framsLib,
        OPTIMIZATION_CRITERIA,
        parsed_args.tournament,
        "1" if parsed_args.genformat is None else parsed_args.genformat,
        parsed_args.initialgenotype,
    )
    pop = toolbox.population(n=parsed_args.popsize)
    hof = tools.HallOfFame(parsed_args.hof_size)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("stddev", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
    start = time()
    pop, log = eaSimple_mut(
        pop,
        toolbox,
        cxpb=parsed_args.pxov,
        mutpb=parsed_args.pmut,
        ngen=parsed_args.generations,
        stats=stats,
        halloffame=hof,
        verbose=True,
        hof_savefile=parsed_args.hof_savefile,
    )
    elapsed = time() - start
    if parsed_args.log_savefile is not None:
        with open(parsed_args.log_savefile, 'wb') as pickle_file:
            pickle.dump(log, pickle_file)
        # Save elasped time to a txt file
        with open(parsed_args.log_savefile[:-4] + '_time.txt', 'w') as time_file:
            time_file.write(str(elapsed))
    print("Best individuals:")
    for ind in hof:
        print(ind.fitness, "\t<--\t", ind[0])
    # Do not save the final solutions to file, as they are already saved in the last generation
    # if parsed_args.hof_savefile is not None:
    #     save_genotypes(parsed_args.hof_savefile, OPTIMIZATION_CRITERIA, hof)


if __name__ == "__main__":
    main()
