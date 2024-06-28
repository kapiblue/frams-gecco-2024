# frams-gecco-2024

This repository stores the code developed by our team for the 2024 Framstics GECCO competition.

The team:

- Agata Żywot
- Zuzanna Gawrysiak
- Bartosz Stachowiak
- Daniel Jankowski
- Kacper Dobek

### Getting started

1. Setup the Framsticks environment according to https://www.framsticks.com/gecco-competition.

2. Clone the repository into the framspy folder.

3. Run the script using the following command (for example):

```bash
python  frams_evolve.py \
        -path FRAMSTICKS_SIMULATOR_PATH \
        -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords-mod.sim" \
        -opt COGpath \
        -popsize 50 \
        -generations 100 \
        -genformat 0 \
        -rand_prob 0.01 \
        -mutator_ub 5.0
```

### The approach

We developed a few mechanisms to improve the basic evolutionary algorithm from DEAP (eaSimple). After a thorough analysis of their performance we decided to use two of them in the submission. Namely, a mechanism that repeats mutation if the evolution process stagnates and another mechanism that supplements the population with randomly generated solutions.

![Comb Results](vis/comb_results.png)

### How to run the algorithm ###

To run the algorithm in a competition mode, please use the following command:

```bash
python  frams_evolve.py \
        -path FRAMSTICKS_SIMULATOR_PATH \
        -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim" \
        -opt COGpath \
        -popsize 50 \
        -generations 2000 \
        -genformat 0 \
        -rand_prob 0.01 \
        -mutator_ub 5.0
```

### Dependencies ###

The algorithm uses no external libraries different than the standard framspy package. However, in the case of problems with a script execution, the `requirements.txt` is provided.
