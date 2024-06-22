import random
from copy import deepcopy
import dataclasses
import json
import time

import deap.algorithms
import deap.tools as tools
import numpy as np


def fitness_reserve(reserve_population, main_population, toolbox):
    """
    Fitness Function for Reserve Population.
    An individual in the reserve population is given a high fitness
    value if its average distance from each of the individuals of the main population is large.
    Therefore the reserve population can provide the main population with additional diversity.

    :param reserve_population: list of individuals in the reserve population
    :param main_population: list of individuals in the main population
    :param toolbox: toolbox used for the evolution
    :return: list of fitness values for each individual in the reserve population
    """
    fitnesses = []
    main_pop_to_compare = [main_ind[0] for main_ind in main_population]
    for res_ind in reserve_population:

        distances = toolbox.dissimilarity(res_ind + main_pop_to_compare)[0, 1:]
        avg_dist_main = np.mean(distances)
        fitnesses.append([avg_dist_main])

    return fitnesses


def evaluate_main_population(
    main_population, toolbox, all: bool = False
) -> tuple[list, int]:
    # MAIN POPULATION: Evaluate the individuals
    if all:
        invalid_ind = main_population
    else:
        invalid_ind = [ind for ind in main_population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
    return main_population, len(invalid_ind)


def evaluate_reserve_population(
    main_population, reserve_population, toolbox, all: bool = False
) -> list:
    # RESERVE POPULATION: Evaluate the individuals
    if all:
        invalid_ind = reserve_population
    else:
        invalid_ind = [ind for ind in reserve_population if not ind.fitness.valid]
    fitnesses = fitness_reserve(invalid_ind, main_population, toolbox)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
    return reserve_population


def save_partial_results(config, hof, log, time_taken, gen):
    print("Saving DPGA output at generation %d to '%s'" % (gen, config.out))
    hof_instances = [
        {"genotype": ind[0], "fitness": ind.fitness.values} for ind in hof
    ]
    result = {
        "hof": hof_instances,
        "log": log,
        "args": dataclasses.asdict(config),
        "time_s": time_taken,
        "gen": gen,
    }
    with open(config.out, "w") as outfile:
        json.dump(result, outfile, default=str)


def dpga(
    population,
    toolbox,
    cxpb,
    mutpb,
    ngen,
    stats=None,
    halloffame=None,
    verbose=__debug__,
    config=None,
    save_period=5,
):
    time_start = time.perf_counter()
    # in the paper: main population = 100, reserve population = 200
    reserve_pop = 0.6
    n = round(reserve_pop * len(population))  # reserve population size
    m = len(population) - n  # main population size

    logbook = tools.Logbook()
    logbook.header = ["gen", "nevals"] + (stats.fields if stats else [])

    # Divide the population into two groups: the main population and the reserve population
    main_population = population[:m]
    reserve_population = population[m:]

    main_population, evaluated = evaluate_main_population(main_population, toolbox)
    reserve_population = evaluate_reserve_population(
        main_population, reserve_population, toolbox
    )

    # STATS AND HALLOFFAME
    if halloffame is not None:
        halloffame.update(main_population)

    record = stats.compile(main_population) if stats else {}
    logbook.record(gen=0, nevals=evaluated, **record)
    if verbose:
        print(logbook.stream)

    # Begin the generational process
    for gen in range(1, ngen + 1):

        # MAIN POPULATION
        # Select the next generation individuals
        main_offspring = toolbox.select(main_population, m)
        # Vary the pool of individuals
        main_offspring = deap.algorithms.varAnd(main_offspring, toolbox, cxpb, mutpb)
        # Evaluate the individuals with an invalid fitness
        main_offspring, evaluated1 = evaluate_main_population(main_offspring, toolbox)

        # RESERVE POPULATION
        # Select the next generation individuals
        reserve_offspring = toolbox.select(reserve_population, n)
        # Vary the pool of individuals
        reserve_offspring = deap.algorithms.varAnd(
            reserve_offspring, toolbox, cxpb, mutpb
        )
        # Evaluate the individuals with an invalid fitness
        reserve_offspring = evaluate_reserve_population(
            main_population, reserve_offspring, toolbox
        )

        # CROSS BREEDING
        # Cross breed between the main and reserve populations
        cross_main_offspring = toolbox.select(main_population, (n - m) // 2)
        cross_reserve_offspring = toolbox.select(reserve_population, (n - m) // 2)
        cross_all_offspring = cross_main_offspring + cross_reserve_offspring
        # Shuffle the offspring
        random.shuffle(cross_all_offspring)
        cross_all_offspring = deap.algorithms.varAnd(
            cross_all_offspring, toolbox, cxpb, mutpb
        )

        # SURVIVAL SELECTION FOR BOTH POPULATIONS
        main_offspring += deepcopy(cross_all_offspring)
        reserve_offspring += deepcopy(cross_all_offspring)

        main_offspring, evaluated2 = evaluate_main_population(
            main_offspring, toolbox, all=True
        )
        main_offspring.sort(key=lambda x: x.fitness.values[0], reverse=True)
        main_offspring = main_offspring[:m]

        reserve_offspring = evaluate_reserve_population(
            main_population, reserve_offspring, toolbox, all=True
        )
        reserve_offspring.sort(key=lambda x: x.fitness.values[0], reverse=True)
        reserve_offspring = reserve_offspring[:n]

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(main_offspring)

        # Replace the current populations by the offspring
        main_population[:] = main_offspring
        reserve_population[:] = reserve_offspring

        # Append the current generation statistics to the logbook
        record = stats.compile(main_population) if stats else {}
        logbook.record(gen=gen, nevals=evaluated1 + evaluated2, **record)
        if verbose:
            print(logbook.stream)

        # Save partial results
        time_taken = time.perf_counter() - time_start
        if gen % save_period == 0:
            save_partial_results(config, halloffame, logbook, time_taken, gen)

    return main_population, logbook
