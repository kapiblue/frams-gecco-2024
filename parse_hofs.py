"""This script is created to parse the Hall of Fame genotypes
from the results files obtained from the experiments.

Parsed genotypes are saved into a single json file that
might be used to initialize the population using 
`-predefined_file` argument in the main script.

The script allows to extract the best genotypes above a 
certain fitness threshold.
"""

import json
import os
import argparse


def parse_hof_file(hof_file: str, threshold: float = 0.0) -> list[str]:
    with open(hof_file, "r") as f:
        data = json.load(f)
        hof = data["hof"]

    best_genotypes = []
    for ind in hof:
        if ind["fitness"][0] >= threshold:
            best_genotypes.append(ind["genotype"])

    return best_genotypes


def main(results_dir: str, threshold: float = 0.0, output: str = "best_genotypes.json"):
    hof_files = [f for f in os.listdir(results_dir) if f.endswith(".json")]

    best_genotypes = []
    for hof_file in hof_files:
        best_genotypes += parse_hof_file(os.path.join(results_dir, hof_file), threshold)

    # remove duplicates
    best_genotypes = list(set(best_genotypes))

    with open(output, "w") as f:
        json.dump(best_genotypes, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-results_dir", type=str, help="Directory with results files")
    parser.add_argument(
        "-threshold",
        type=float,
        default=0.0,
        help="Threshold for fitness value. Default: 0.0",
    )
    parser.add_argument(
        "-output",
        type=str,
        default="best_genotypes.json",
        help="Output file for the best genotypes. Default: best_genotypes.json",
    )
    args = parser.parse_args()

    main(args.results_dir, args.threshold, args.output)

    