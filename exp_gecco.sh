#!/bin/bash

lib_path=/Users/kacperdobek/Documents/Studia/Magisterskie/Semester1/BIAM/framstics/Framsticks50rc29

echo $lib_path

for i in 0 1
do
   for j in {1..10}
   do
      python FramsticksEvolutionComp.py -path $lib_path \
      -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim" \
      -opt COGpath \
      -genformat $i \
      -popsize 30 \
      -generations 50 \
      -hof_size 1 \
      -hof_savefile hofs/HoF-f$i-$j.gen \
      -log_savefile logs/log-f$i-run-$j.pkl
   done
done

echo "All experiments completed."