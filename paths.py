import pathlib

FRAMSPY_DIR = pathlib.Path(__file__).parent.parent.resolve()
FRAMS_GECCO_DIR = pathlib.Path(__file__).parent.resolve()
RESULTS_DIR = FRAMS_GECCO_DIR / "results"
INTERPRETER = FRAMSPY_DIR.parent / ".venv/Scripts/python.exe"
FRAMLIB_DIR = "D:\\Programs\\Framsticks\\"
