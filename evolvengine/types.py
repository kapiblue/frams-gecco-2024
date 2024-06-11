from __future__ import annotations

import argparse
import typing
import dataclasses

import enum
import deap.base
import deap.tools


class MetaAlgorithm(enum.Enum):
    SIMPLE = "SIMPLE"
    MU_PLUS_LAMBDA = "MU_PLUS_LAMBDA"
    MU_COMMA_LAMBDA = "MU_COMMA_LAMBDA"

    def __str__(self):
        return self.value


class FramsticksLibInterface(typing.Protocol):
    def evaluate(self, genotype: str) -> dict: ...
    def crossOver(self, genotype1: str, genotype2: str) -> str: ...
    def mutate(self, genotypes: list[str]) -> list[str]: ...
    def getSimplest(self, genetic_format: str) -> str: ...


class EvolutionaryAlgorithm(typing.Protocol):
    def __call__(
        self,
        population: list[Individual],
        toolbox: deap.base.Toolbox,
        cxpb: float,
        mutpb: float,
        ngen: int,
        stats: deap.tools.Statistics,
        halloffame: deap.tools.HallOfFame,
        verbose: bool,
    ) -> tuple[list[Individual], dict]: ...


@dataclasses.dataclass
class RunConfig:
    path: str
    sim: str
    genformat: str
    initialgenotype: str | None
    opt: list[str]
    popsize: int
    generations: int
    tournament: int
    pmut: int
    pxov: int
    hof_size: int
    max_numparts: int
    max_numjoints: int
    max_numneurons: int
    max_numconnections: int
    max_numgenochars: int
    seed: int
    out: str | None
    meta: MetaAlgorithm
    lambda_: int
    mutator_ub: float
    opt_func: int

    def __post_init__(self):
        if not isinstance(self.opt, list):
            self.opt = self.opt.split(",")

    @classmethod
    def from_args(cls) -> RunConfig:
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
            "-generations",
            type=int,
            default=5,
            help="Number of generations, default: 5.",
        )
        parser.add_argument(
            "-tournament", type=int, default=5, help="Tournament size, default: 5."
        )
        parser.add_argument(
            "-pmut",
            type=float,
            default=0.8,
            help="Probability of mutation, default: 0.8",
        )
        parser.add_argument(
            "-pxov",
            type=float,
            default=0.2,
            help="Probability of crossover, default: 0.2",
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
            default="output.json",
            help="If set, the Hall of Fame and log will be saved in this location. Must be .json",
        )
        parser.add_argument(
            "-meta",
            type=MetaAlgorithm,
            default=MetaAlgorithm.SIMPLE,
            choices=MetaAlgorithm,
            help="Evolutionary algorithm to use. Default: SIMPLE",
        )
        parser.add_argument(
            "-lambda_",
            type=float,
            default=0.8,
            help="lambda parameter for evolutionary algorithm. Default: 1",
        )
        parser.add_argument(
            "-mutator_ub",
            type=float,
            default=1,
            help="Upper bound for mutation strenth. Default: 1.0 (strenth will not increase)",
        )
        parser.add_argument(
            "-opt_func",
            type=int,
            default=3,
            help="Optimization function. Default: 3 (Same default as in FramsticksLibCompetition).",
        )
        args = parser.parse_args()
        return cls(**vars(args))


Individual = list[str]  # 1-sized string genotype
ToolboxProcessor = typing.Callable[
    [deap.base.Toolbox, FramsticksLibInterface, RunConfig], deap.base.Toolbox
]
Mutator = typing.Callable[[FramsticksLibInterface, Individual], tuple[Individual]]
