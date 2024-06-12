import itertools
import subprocess
import multiprocessing as mp
import signal
import tqdm
import paths

EXPERIMENT = "rand"
N_REPS = 10
RAND_PROBS = [0, 0.001, 0.01, 0.05, 0.1, 0.5]
FUNCS = ["3", "4", "5"]
REPRESENTATIONS = ["0", "1"]


def resolve_filename(func: str, prob: float, repr: str, repeat: int):
    return paths.RESULTS_DIR / EXPERIMENT / f"func{func}-r{prob}-f{repr}-{repeat}.json"


def run_command(func: str, prob: float, repr: str, repeat: int):
    args = [
        paths.INTERPRETER,
        str(paths.FRAMS_GECCO_DIR / "frams_evolve.py"),
        "-path",
        paths.FRAMLIB_DIR,
        "-sim",
        f"eval-allcriteria.sim;deterministic.sim;recording-body-coords-mod.sim",
        "-opt",
        "COGpath",
        "-popsize",
        "50",
        "-generations",
        "100",
        "-genformat",
        repr,
        "-out",
        resolve_filename(func, prob, repr, repeat),
        "-rand_prob",
        str(prob),
        "-opt_func",
        func,
        "-seed",
        str(repeat),
    ]
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
    if not (paths.RESULTS_DIR / EXPERIMENT).exists():
        (paths.RESULTS_DIR / EXPERIMENT).mkdir(parents=True)
    configs = list(itertools.product(FUNCS, RAND_PROBS, REPRESENTATIONS, range(N_REPS)))
    configs = [c for c in configs if not resolve_filename(*c).exists()]

    nproc = max(mp.cpu_count() - 2, 1)
    print(f"Running {len(configs)} simulations on {nproc} processes...")
    with mp.Pool(nproc, initializer) as pool, tqdm.tqdm(total=len(configs)) as pbar:
        for _ in pool.imap_unordered(run_packed, configs):
            pbar.update()

    print("Done!")


if __name__ == "__main__":
    print()
    main()
