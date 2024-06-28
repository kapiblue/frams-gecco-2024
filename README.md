# frams-gecco-2024

Repository for the 2024 Framstics GECCO competition.

Team:

- Agata Żywot
- Zuzanna Gawrysiak
- Bartosz Stachowiak
- Daniel Jankowski
- Kacper Dobek


### Getting started

1. Setup the Framsticks environment according to https://www.framsticks.com/gecco-competition.

2. Clone the repository into your framspy folder.

3. Run the script using the following command (for example):

```bash
python  frams_evolve.py \
        -path FRAMSTICKS_SIMULATOR_PATH \
        -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords-mod.sim" \
        -opt COGpath \
        -popsize 50 \
        -generations 100 \
        -genformat 0 \
        -temp 100 \
        -mutator_ub 5.0
```
