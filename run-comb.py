import itertools
import subprocess
import multiprocessing as mp
import signal
import tqdm
import paths

EXPERIMENT = "comb"
N_REPS = 10


def resolve_filename(
    dpga_enabled: int,
    sa_enabled: int,
    rand_enabled: int,
    vs_enabled: int,
    pp_enabled: int,
    repeat: int,
):
    return (
        paths.RESULTS_DIR
        / EXPERIMENT
        / f"DPGA{dpga_enabled}-SA{sa_enabled}-R{rand_enabled}-VS{vs_enabled}-PP{pp_enabled}-{repeat}.json"
    )


def run_command(
    dpga_enabled: int,
    sa_enabled: int,
    rand_enabled: int,
    vs_enabled: int,
    pp_enabled: int,
    repeat: int,
):
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
        "0",
        "-out",
        resolve_filename(
            dpga_enabled, sa_enabled, rand_enabled, vs_enabled, pp_enabled, repeat
        ),
        "-seed",
        str(repeat),
    ]
    if dpga_enabled:
        args.extend(["-meta", "DPGA"])
    if sa_enabled:
        args.extend(["-temp", "100"])
    if rand_enabled:
        args.extend(["-rand_prob", "0.01"])
    if vs_enabled:
        args.extend(["-mutator_ub", "5.0"])
    if pp_enabled:
        args.extend(["-predefined_file", "best_genotypes.json"])
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

    # run all combinations of the following parameters
    # DPGA, SA, RAND, VS, PP

    configs = list(itertools.product(*list(itertools.repeat((0, 1), 5)), range(N_REPS)))
    configs = [c for c in configs if not resolve_filename(*c).exists()]

    nproc = max(mp.cpu_count() - 2, 1)
    print(f"Running {len(configs)} simulations on {nproc} processes...")
    with mp.Pool(nproc, initializer) as pool, tqdm.tqdm(total=len(configs)) as pbar:
        for _ in pool.imap_unordered(run_packed, configs):
            pbar.update()

    print("Done!")


if __name__ == "__main__":
    main()
