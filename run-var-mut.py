import itertools
import subprocess
import multiprocessing as mp
import signal
import tqdm
import paths

N_REPS = 10
STRENGTHS = [1, 1.5, 2, 3, 5, 10]
REPRESENTATIONS = ["0", "1"]


def resolve_filename(strength: float, repr: str, repeat: int):
    return paths.RESULTS_DIR / "var-mut" / f"s{strength}-{repr}-{repeat}.json"


def run_command(strength: float, repr: str, repeat: int):
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
        "-mutator_ub",
        str(strength),
        "-out",
        resolve_filename(strength, repr, repeat),
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
    configs = list(itertools.product(STRENGTHS, REPRESENTATIONS, range(N_REPS)))
    configs = [c for c in configs if not resolve_filename(*c).exists()]

    nproc = max(mp.cpu_count() - 2, 1)
    print(f"Running {len(configs)} simulations on {nproc} processes...")
    with mp.Pool(nproc, initializer) as pool, tqdm.tqdm(total=len(configs)) as pbar:
        for _ in pool.imap_unordered(run_packed, configs):
            pbar.update()

    print("Done!")


if __name__ == "__main__":
    print()
