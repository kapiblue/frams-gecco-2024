import os
from typing import List, Callable, Union

from evolalg_steps.base.step import Step
import pickle
import time

from evolalg_steps.base.union_step import UnionStep
from evolalg_steps.selection.selection import Selection
from evolalg_steps.utils.stable_generation import StableGeneration
import logging
import pandas as pd

class Experiment:
    def __init__(self, init_population: List[Callable],
                 selection: Selection,
                 new_generation_steps: List[Union[Callable, Step]],
                 generation_modification: List[Union[Callable, Step]],
                 end_steps: List[Union[Callable, Step]],
                 population_size,
                 checkpoint_path=None, checkpoint_interval=None,
                 log_savefile=None):

        self.init_population = init_population
        self.running_time = 0
        self.step = StableGeneration(
            selection=selection,
            steps=new_generation_steps,
            population_size=population_size)
        self.generation_modification = UnionStep(generation_modification)

        self.end_steps = UnionStep(end_steps)

        self.checkpoint_path = checkpoint_path
        self.checkpoint_interval = checkpoint_interval
        self.generation = 0
        self.population = None
        self.fitness_log = []
        self.log_savefile = log_savefile

    def init(self):
        self.generation = 0
        for s in self.init_population:
            if isinstance(s, Step):
                s.init()

        self.step.init()
        self.generation_modification.init()
        self.end_steps.init()
        self.population = []
        for s in self.init_population:
            self.population = s(self.population)

    def run(self, num_generations):
        for i in range(self.generation + 1, num_generations + 1):
            start_time = time.time()
            self.generation = i
            self.population = self.step(self.population)
            self.population = self.generation_modification(self.population)
            self.running_time += time.time() - start_time

            for individual in self.population:
                fitness = individual.fitness  # Assuming each individual has a fitness attribute
                self.fitness_log.append([i, *fitness.getValues()])
            
            if (self.checkpoint_path is not None
                    and self.checkpoint_interval is not None
                    and i % self.checkpoint_interval == 0):
                self.save_checkpoint()
        df = pd.DataFrame(self.fitness_log, columns=["generation", "dissim", "cog"])
        df.to_csv(self.log_savefile)
        with open(self.log_savefile[:-4] + "-time.txt", "w") as time_file:
            time_file.write(str(self.running_time))

        self.population = self.end_steps(self.population)

    def save_checkpoint(self):
        tmp_filepath = self.checkpoint_path+"_tmp"
        try:
            with open(tmp_filepath, "wb") as file:
                pickle.dump(self, file)
            os.replace(tmp_filepath, self.checkpoint_path)  # ensures the new file was first saved OK (e.g. enough free space on device), then replace
        except Exception as ex:
            raise RuntimeError("Failed to save checkpoint '%s' (because: %s). This does not prevent the experiment from continuing, but let's stop here to fix the problem with saving checkpoints." % (tmp_filepath, ex))


    @staticmethod
    def restore(path):
        with open(path) as file:
            res = pickle.load(file)
        return res
