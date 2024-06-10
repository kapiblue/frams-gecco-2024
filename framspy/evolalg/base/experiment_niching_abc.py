import time
from abc import ABC, abstractmethod

import numpy as np
from deap import base, tools
from deap.tools.emo import assignCrowdingDist

from ..constants import BAD_FITNESS
from ..structures.individual import Individual
from .experiment_abc import ExperimentABC
from .remove_diagonal import remove_diagonal


class DeapFitness(base.Fitness):
    weights = (1, 1)

    def __init__(self, *args, **kwargs):
        super(DeapFitness, self).__init__(*args, **kwargs)


class ExperimentNiching(ExperimentABC, ABC):
    fit: str = "niching"
    normalize: str = "None"
    archive_size: int = None

    def __init__(self, fit, normalize, popsize, hof_size, save_only_best, knn_niching, knn_nslc, archive_size) -> None:
        ExperimentABC.__init__(self,popsize=popsize, hof_size=hof_size, save_only_best=save_only_best)
        self.fit = fit
        self.normalize = normalize
        self.knn_niching = knn_niching # this parameter is used for local novelty and local niching
        self.knn_nslc = knn_nslc
        self.archive_size=archive_size

        # np.argpartition requires these parameters to be at most popsize-2; popsize is decreased by 1 because we remove_diagonal()
        if self.knn_niching > popsize - 2:
            raise ValueError("knn_niching (%d) should be at most popsize-2 (%d)" % (self.knn_niching, popsize-2))
        if self.knn_nslc > popsize - 2:
            raise ValueError("knn_nslc (%d) should be at most popsize-2 (%d)" % (self.knn_nslc, popsize-2))


    def transform_indexes(self, i, index_array):
        return [x+1 if x >= i else x for x in index_array]

    def normalize_dissim(self, dissim_matrix):
        dissim_matrix = remove_diagonal(np.array(dissim_matrix)) # on the diagonal we usually have zeros (an individual is identical with itself, so the dissimilarity is 0). In some techniques we need to find "k" most similar individuals, so we remove the diagonal so that self-similarity of individuals does not interfere with finding "k" other most similar individuals. The matrix from square n*n turns into n*(n-1).
        if self.normalize == "none":
            return dissim_matrix
        elif self.normalize == "max":
            divide_by = np.max(dissim_matrix)
        elif self.normalize == "sum":
            divide_by = np.sum(dissim_matrix)
        else:
            raise ValueError("Wrong normalization method: '%s'" % self.normalize)
        if divide_by != 0:
            return dissim_matrix/divide_by
        else:
            return dissim_matrix

    def do_niching(self, population_structures):
        population_archive = population_structures.population + population_structures.archive
        dissim_matrix = self.dissimilarity(population_archive)
        if "knn" not in self.fit:
            dissim_list = np.mean(self.normalize_dissim(dissim_matrix), axis=1)
        else:
            dissim_list = np.mean(np.partition(
                self.normalize_dissim(dissim_matrix), self.knn_niching)[:, :self.knn_niching], axis=1)

        if Individual.fitness_set_negative_to_zero is False and ("niching" in self.fit or "novelty" in self.fit):
        	raise ValueError("Negative fitness values not tested in combination with niching or novelty. When using these techniques, verify formulas or consider using the flag -fitness_set_negative_to_zero") # once the formulas are verified/improved, the command-line flag and this conditional check can be removed.

        if "niching" in self.fit:
            for i, d in zip(population_archive, dissim_list):
                print(i.genotype)
                print(i.rawfitness)
                i.fitness = i.rawfitness * d
        elif "novelty" in self.fit:
            for i, d in zip(population_archive, dissim_list):
                i.fitness = d
        else:
            raise ValueError("Unsupported fit type: '%s'. Use the correct type or implement a new behavior." % self.fit)
        population_structures.update_archive(dissim_matrix, population_archive)

    def do_nsga2_dissim(self, population):
        dissim_matrix = self.dissimilarity(population)
        dissim_list = np.mean(self.normalize_dissim(dissim_matrix), axis=1)
        for i, d in zip(population, dissim_list):
            i.fitness = DeapFitness(tuple((d, i.rawfitness)))

    def do_nslc_dissim(self, population_structures, pop_offspring):
        population_archive = population_structures.archive + pop_offspring
        dissim_matrix = self.dissimilarity(population_archive)
        normalized_matrix = self.normalize_dissim(dissim_matrix)
        for i in range(len(normalized_matrix)):
            temp_dissim = normalized_matrix[i]
            index_array = np.argpartition(temp_dissim, kth=self.knn_nslc, axis=-1)[:self.knn_nslc]
            dissim_value = np.mean(np.take_along_axis(
                temp_dissim, index_array, axis=-1))
            temp_fitness = population_archive[i].rawfitness
            population_of_most_similar = list(
                map(population_archive.__getitem__, self.transform_indexes(i, index_array)))
            temp_ind_fit = sum(
                [1 for ind in population_of_most_similar if ind.rawfitness < temp_fitness])
            population_archive[i].fitness = DeapFitness(
                tuple((dissim_value, temp_ind_fit)))
        population_structures.update_archive(dissim_matrix, population_archive)

    def make_new_population_nsga2(self, population_structures, prob_mut, prob_xov):
        expected_mut = int(self.popsize * prob_mut)
        expected_xov = int(self.popsize * prob_xov)
        assert expected_mut + expected_xov <= self.popsize, "If probabilities of mutation (%g) and crossover (%g) added together exceed 1.0, then the population would grow every generation..." % (prob_mut, prob_xov)
        assignCrowdingDist(population_structures.population)
        offspring = tools.selTournamentDCD(population_structures.population, self.popsize)

        def addGenotypeIfValid(ind_list, genotype):
            new_individual = Individual()
            new_individual.set_and_evaluate(genotype, self.evaluate)
            if new_individual.fitness is not BAD_FITNESS:
                ind_list.append(new_individual)

        counter = 0

        def get_individual(pop, c):
            if c < len(pop):
                ind = pop[c]
                c += 1
                return ind, c
            else:
                c = 0
                ind = pop[c]
                c += 1
                return ind, c

        newpop = []
        while len(newpop) < expected_mut:
            ind, counter = get_individual(offspring, counter)
            addGenotypeIfValid(newpop, self.mutate(ind.genotype))

        # adding valid crossovers of selected individuals...
        while len(newpop) < expected_mut + expected_xov:
            ind1, counter = get_individual(offspring, counter)
            ind2, counter = get_individual(offspring, counter)
            addGenotypeIfValid(newpop, self.cross_over(ind1.genotype, ind2.genotype))

        # select clones to fill up the new population until we reach the same size as the input population
        while len(newpop) < len(population_structures.population):
            ind, counter = get_individual(offspring, counter)
            newpop.append(Individual().copyFrom(ind))

        pop_offspring = population_structures.population + newpop # used both for nsga2 and nslc 
        # print(len(pop_offspring)) # for debugging
        if self.fit == "nslc":
            self.do_nslc_dissim(population_structures, pop_offspring)
        elif self.fit == "nsga2":
            self.do_nsga2_dissim(pop_offspring)
        out_pop = tools.selNSGA2(pop_offspring, len(population_structures.population))
        return out_pop

    def evolve(self, hof_savefile, generations, initialgenotype, pmut, pxov, tournament_size):
        file_name = self.get_state_filename(hof_savefile)
        state = self.load_state(file_name)
        if state is not None:  # loaded state from file
            # saved generation has been completed, start with the next one
            self.current_generation += 1
            print("...Resuming from saved state: population size = %d, hof size = %d, stats size = %d, archive size = %d, generation = %d/%d" % (len(self.population_structures.population), len(self.hof), len(self.stats), (len(self.population_structures.archive)), self.current_generation, generations))  # self.current_generation (and g) are 0-based, parsed_args.generations is 1-based
        else:
            self.initialize_evolution(self.genformat, initialgenotype)

        time0 = time.process_time()
        for g in range(self.current_generation, generations):
            if self.fit != "raw" and self.fit != "nsga2" and self.fit != "nslc":
                print("Niching...")
                self.do_niching(self.population_structures)

            if type(self.population_structures.population[0].fitness) == DeapFitness:
                self.population_structures.population = self.make_new_population_nsga2(  # used both for nsga2 and nslc
                    self.population_structures, pmut, pxov)
            else:
                self.population_structures.population = self.make_new_population(
                    self.population_structures.population, pmut, pxov, tournament_size)

            self.update_stats(g, self.population_structures.population)

            if hof_savefile is not None:
                self.current_generation = g
                self.time_elapsed += time.process_time() - time0
                self.save_state(file_name)
        if hof_savefile is not None:
            self.save_genotypes(hof_savefile)
        return self.population_structures.population, self.stats

    @staticmethod
    def get_args_for_parser():
        parser = ExperimentABC.get_args_for_parser()
        parser.add_argument("-dissim",type= int, default=1,
                   help="Dissimilarity measure type. Available: -3:freq, -2:dens, -1:Leven, 1:frams-struct (default}, 2:frams-descr")
        parser.add_argument("-fit",type= str, default="raw",
                        help="Fitness type, availible types: niching, novelty, knn_niching (local), knn_novelty (local), nsga2, nslc and raw (default)")
        parser.add_argument("-archive",type= int, default=50, help="Maximum archive size")
        parser.add_argument("-normalize",type= str, default= "max",
                            help="What normalization to use for the dissimilarity matrix: max (default}, sum, or none")
        parser.add_argument("-knn_niching",type= int, default=5,
                        help="The number of nearest neighbors for local novelty/niching. If knn==0, global is performed. Default: 5")
        parser.add_argument("-knn_nslc",type= int, default=5,
                        help="The number of nearest neighbors for NSLC. If knn==0, global is performed. Default: 5")
        return parser 
        
    @abstractmethod
    def dissimilarity(self, population: list):
        pass
