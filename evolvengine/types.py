from __future__ import annotations

import argparse
import typing
import dataclasses

import deap.base


class FramsticksLibInterface(typing.Protocol):
    def evaluate(self, genotype: str) -> dict: ...
    def crossOver(self, genotype1: str, genotype2: str) -> str: ...
    def mutate(self, genotypes: list[str]) -> list[str]: ...
    def getSimplest(self, genetic_format: str) -> str: ...


@dataclasses.dataclass
class Args:
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

    def __post_init__(self):
        if not isinstance(self.opt, list):
            self.opt = self.opt.split(",")

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Args:
        return cls(**vars(args))


Individual = list[str]  # 1-sized string genotype
ToolboxProcessor = typing.Callable[
    [deap.base.Toolbox, FramsticksLibInterface, Args], deap.base.Toolbox
]
