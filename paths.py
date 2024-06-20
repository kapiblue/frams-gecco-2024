import pathlib
import sys

is_win = sys.platform.startswith("win")

FRAMSPY_DIR = pathlib.Path(__file__).parent.parent.resolve()
FRAMS_GECCO_DIR = pathlib.Path(__file__).parent.resolve()
RESULTS_DIR = FRAMS_GECCO_DIR / "results"
if is_win:
    INTERPRETER = FRAMSPY_DIR.parent / ".venv/Scripts/python.exe"
    FRAMLIB_DIR = "D:\\Programs\\Framsticks\\"
else:
    INTERPRETER = "python"
    FRAMLIB_DIR = "/home/sbartekt/Framsticks50rc30/"
