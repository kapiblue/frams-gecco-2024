#!/bin/bash

# IMPORTANT: open the framspy folder in the terminal and run the script from there

lib_path=/Users/kacperdobek/Documents/Studia/Magisterskie/Semester1/BIAM/framstics/Framsticks50rc29

# evolution with niching
for i in 0 1
do
   for j in {1..10}
   do
       python -m evolalg.run_frams_niching  -path $lib_path \
       -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim" \
       -opt COGpath -genformat $i -dissim 1 -fit knn_niching -archive 50 \
       -fitness_set_negative_to_zero  -max_numparts 15 -max_numneurons 15 \
       -max_numjoints 30 -max_numconnections 30  -max_numgenochars 10000 \
       -popsize 30 -generations 50 -normalize none -hof_size 1 \
       -hof_savefile frams-gecco-2024/hofs_baseline/HoF-f$i-$j.gen \
       -log_savefile frams-gecco-2024/logs_baseline/log-f$i-run-$j.pkl
       done
done

echo "All experiments completed."