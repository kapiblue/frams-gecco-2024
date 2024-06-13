#!/bin/bash

# IMPORTANT: open the framspy folder in the terminal and run the script from there

lib_path=/Users/kacperdobek/Documents/Studia/Magisterskie/Semester1/BIAM/framstics/Framsticks50rc29

# evolution with niching
for i in 0 1
do
   for j in {1..10}
   do
       python -m evolalg_steps.examples.multicriteria  -path $lib_path \
       -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim" \
       -opt "COGpath,levenshtein" -genformat $i -dissim levenshtein \
       -popsize 32 -generations 50 -hof_size 1 \
       -log_savefile ../logs_nsga/log-f$i-run-$j.csv
       done
done

echo "All experiments completed."