import typing

import numpy as np
import deap.base
import deap.tools
import deap.creator

from . import types


def genotype_within_constraint(
    genotype: str,
    dict_criteria_values: dict[str, float],
    criterion_name: str,
    constraint_value: float,
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


def frams_evaluate(
    frams_lib: types.FramsticksLibInterface,
    args: types.RunConfig,
    individual: types.Individual,
) -> typing.Union[list[float], float]:
    # fitness of -1 is intended to discourage further propagation of this genotype via selection ("this genotype is very poor")
    BAD_FITNESS = [-1] * len(args.opt)

    # individual[0] because we can't (?) have a simple str as a deap genotype/individual, only list of str.
    genotype = individual[0]

    data = frams_lib.evaluate([genotype])
    # print("Evaluated '%s'" % genotype, 'evaluation is:', data)
    valid = True
    try:
        first_genotype_data = data[0]
        evaluation_data = first_genotype_data["evaluations"]
        default_evaluation_data = evaluation_data[""]
        fitness = [default_evaluation_data[crit] for crit in args.opt]
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
        default_evaluation_data["numgenochars"] = len(
            genotype
        )  # for consistent constraint checking below
        criteria = [
            "numparts",
            "numjoints",
            "numneurons",
            "numconnections",
            "numgenochars",
        ]
        valid = all(
            genotype_within_constraint(
                genotype, default_evaluation_data, crit, getattr(args, "max_" + crit)
            )
            for crit in criteria
        )
    if not valid:
        fitness = BAD_FITNESS
    return fitness


def frams_crossover(
    frams_lib: types.FramsticksLibInterface,
    individual1: types.Individual,
    individual2: types.Individual,
) -> tuple[types.Individual, types.Individual]:
    geno1 = individual1[0]
    geno2 = individual2[0]
    individual1[0] = frams_lib.crossOver(geno1, geno2)
    individual2[0] = frams_lib.crossOver(geno1, geno2)
    return individual1, individual2


def frams_mutate(
    frams_lib: types.FramsticksLibInterface, individual: types.Individual
) -> tuple[types.Individual]:
    individual[0] = frams_lib.mutate([individual[0]])[0]
    return (individual,)


def frams_getsimplest(
    frams_lib: types.FramsticksLibInterface,
    genetic_format: str,
    initial_genotype: str = None,
):
    return (
        initial_genotype
        if initial_genotype is not None
        else frams_lib.getSimplest(genetic_format)
    )


def setup_toolbox(
    frams_lib: types.FramsticksLibInterface, config: types.RunConfig
) -> deap.base.Toolbox:
    deap.creator.create(
        "FitnessMax", deap.base.Fitness, weights=[1.0] * len(config.opt)
    )
    deap.creator.create("Individual", list, fitness=deap.creator.FitnessMax)
    toolbox = deap.base.Toolbox()
    toolbox.register(
        "attr_simplest_genotype",
        frams_getsimplest,
        frams_lib,
        config.genformat,
        config.initialgenotype,
    )
    toolbox.register(
        "individual",
        deap.tools.initRepeat,
        deap.creator.Individual,
        toolbox.attr_simplest_genotype,
        1,
    )
    toolbox.register("population", deap.tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", frams_evaluate, frams_lib, config)
    toolbox.register("mate", frams_crossover, frams_lib)
    toolbox.register("mutate", frams_mutate, frams_lib)
    toolbox.register("select", deap.tools.selTournament, tournsize=config.tournament)
    if len(config.opt) > 1:
        toolbox.register("select", deap.tools.selNSGA2)
    return toolbox


def setup_stats() -> deap.tools.Statistics:
    stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("stddev", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    return stats
