import dataclasses
import glob
import json
import pathlib
import typing

import pandas as pd
import numpy as np


@dataclasses.dataclass
class GenInstance:
    genotype: str
    fitness: float


@dataclasses.dataclass
class HistoryEntry:
    gen: int
    nevals: int
    avg: float
    stddev: float
    min: float
    max: float


@dataclasses.dataclass
class RunResult:
    history: list[HistoryEntry]
    time_s: float
    best_instances: list[GenInstance]

    @property
    def cum_nevals(self) -> np.ndarray:
        return np.cumsum([x.nevals for x in self.history])


def import_from_dir(
    dir: str | pathlib.Path,
    grouper: typing.Callable[
        [dict[str, typing.Any]],
        str,
    ],
) -> dict[str, RunResult]:
    if isinstance(dir, str):
        dir = pathlib.Path(dir)
    if not dir.exists():
        raise FileNotFoundError(f"Directory {dir} does not exist.")
    result_files = glob.glob(str(dir / "*.json"))
    results = {}
    for file in result_files:
        with open(file, "r") as f:
            data = json.load(f)
        best_instances = [
            GenInstance(x["genotype"], x["fitness"][0]) for x in data["hof"]
        ]
        history_entries = [HistoryEntry(**x) for x in data["log"]]
        run_res = RunResult(
            history=history_entries,
            time_s=data["time_s"],
            best_instances=best_instances,
        )
        group_name = grouper(data["args"])
        if group_name not in results:
            results[group_name] = []
        results[group_name].append(run_res)
    return results


def convert_to_dataframe(grouped_results: dict[str, list[RunResult]]) -> pd.DataFrame:
    pre_df = []
    for group_name, results in grouped_results.items():
        for run_idx, run_res in enumerate(results):
            for entry in run_res.history:
                pre_df.append(
                    {
                        "group": group_name,
                        "run_idx": run_idx,
                        "gen": entry.gen,
                        "nevals": entry.nevals,
                        "avg": entry.avg,
                        "stddev": entry.stddev,
                        "min": entry.min,
                        "max": entry.max,
                        "time_s": run_res.time_s,
                    }
                )
    return pd.DataFrame(pre_df)
