#from FramsticksLib import FramsticksLib

from FramsticksLibCompetition import FramsticksLibCompetition as FramsticksLib

from .structures.individual import Individual

from .frams_base.experiment_frams_niching import ExperimentFramsNiching

from time import time
import argparse
import pickle

def main():
    # random.seed(123)  # see FramsticksLib.DETERMINISTIC below, set to True if you want full determinism
    # must be set before FramsticksLib() constructor call
    FramsticksLib.DETERMINISTIC = False
    parsed_args = ExperimentFramsNiching.get_args_for_parser().parse_args()
    parser = argparse.ArgumentParser()
    parser.add_argument("-log_savefile", required=False,help="If set, the log will be saved in this location. Must be .pkl",
                            type=str)
    log_savefile = parsed_args.log_savefile
    Individual.fitness_set_negative_to_zero = parsed_args.fitness_set_negative_to_zero # setting the "static" field once
    print("Argument values:", ", ".join(
        ['%s=%s' % (arg, getattr(parsed_args, arg)) for arg in vars(parsed_args)]))
    # multiple criteria not supported here. If needed, use FramsticksEvolution.py
    opt_criteria = parsed_args.opt.split(",")
    framsLib = FramsticksLib(
        parsed_args.path, parsed_args.lib, parsed_args.sim)
    constrains = {"max_numparts": parsed_args.max_numparts,
                  "max_numjoints": parsed_args.max_numjoints,
                  "max_numneurons": parsed_args.max_numneurons,
                  "max_numconnections": parsed_args.max_numconnections,
                  "max_numgenochars": parsed_args.max_numgenochars,
                  }

    experiment = ExperimentFramsNiching(frams_lib=framsLib,
                                        optimization_criteria=opt_criteria,
                                        hof_size=parsed_args.hof_size,
                                        constraints=constrains,
                                        normalize=parsed_args.normalize,
                                        dissim=parsed_args.dissim,
                                        fit=parsed_args.fit,
                                        genformat=parsed_args.genformat,
                                        popsize=parsed_args.popsize,
                                        archive_size=parsed_args.archive,
                                        save_only_best=parsed_args.save_only_best,
                                        knn_niching=parsed_args.knn_niching,
                                        knn_nslc=parsed_args.knn_nslc)

    start = time()
    pop, log = experiment.evolve(hof_savefile=parsed_args.hof_savefile,
                                 generations=parsed_args.generations,
                                 initialgenotype=parsed_args.initialgenotype,
                                 pmut=parsed_args.pmut,
                                 pxov=parsed_args.pxov,
                                 tournament_size=parsed_args.tournament)
    elapsed = time() - start
    if log_savefile is not None:
        with open(parsed_args.log_savefile, "wb") as pickle_file:
            pickle.dump(log, pickle_file)
        # Save elasped time to a txt file
        with open(parsed_args.log_savefile[:-4] + "-time.txt", "w") as time_file:
            time_file.write(str(elapsed))


if __name__ == "__main__":
    main()
