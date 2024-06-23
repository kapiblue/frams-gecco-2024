from . import types
import deap.base
import deap.creator
import deap.tools
import json


class Predefiner:
    def __init__(
        self,
        lib: types.FramsticksLibInterface,
        genformat: str,
        gen_path: str,
    ) -> None:
        self.lib = lib
        self.genformat = genformat
        self.gen_path = gen_path

        self.genotypes = [] if gen_path is None else self.__load_genotypes()

    def __load_genotypes(self) -> list[str]:
        """Load predefined genotypes from file

        Returns:
            list[str]: list of genotypes
        """
        with open(self.gen_path, "r") as f:
            genotypes = json.load(f)
        return genotypes

    # NOTE: without parameter n, the function does not work
    # properly under the deap framework.
    def get_population(self, n: int) -> list[types.Individual]:
        """Generate initial population of individuals
        with predefined genotypes and simplest genotypes

        Returns:
            list[types.Individual]: initial population
        """
        pop = []

        # add predefined genotypes
        for gen in self.genotypes:
            ind = deap.creator.Individual([gen])
            pop.append(ind)

        # fill the rest of the population with simplest genotypes
        while len(pop) < n:
            gen = self.lib.getSimplest(self.genformat)
            ind = deap.creator.Individual([gen])
            pop.append(ind)

        return pop[:n]
