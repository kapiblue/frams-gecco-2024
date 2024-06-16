import itertools
import multiprocessing as mp
import signal
import subprocess

import tqdm

import paths

N_REPS = 10
ALGS = ["DPGA"]
REPRESENTATIONS = ["0"]


def resolve_filename(alg: str, repr: str, repeat: int):
    return paths.RESULTS_DIR / "dpga_defined" / f"{alg}-{repr}-{repeat}.json"


def run_command(alg: str, repr: str, repeat: int):
    args = [
        paths.INTERPRETER,
        str(paths.FRAMS_GECCO_DIR / "frams_evolve.py"),
        "-path",
        paths.FRAMLIB_DIR,
        "-sim",
        f"eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim",
        "-opt",
        "COGpath",
        "-popsize",
        "50",
        "-generations",
        "100",
        "-genformat",
        repr,
        "-meta",
        alg,
        "-out",
        resolve_filename(alg, repr, repeat),
        "-seed",
        str(repeat),
        "-predefined_file",
        "best_genotypes.json",
    ]
    if alg == "MU_COMMA_LAMBDA":
        args.extend(["-lambda_", "1.2"])
    result = subprocess.run(
        args,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stderr.decode())


def run_packed(args):
    return run_command(*args)


def initializer():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def main():
    configs = list(itertools.product(ALGS, REPRESENTATIONS, range(N_REPS)))
    configs = [c for c in configs if not resolve_filename(*c).exists()]

    nproc = 10
    print(f"Running {len(configs)} simulations on {nproc} processes...")
    with mp.Pool(nproc, initializer) as pool, tqdm.tqdm(total=len(configs)) as pbar:
        for _ in pool.imap_unordered(run_packed, configs):
            pbar.update()

    print("Done!")


if __name__ == "__main__":
    print()
    main()
