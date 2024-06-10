#!/bin/sh

DIR_WITH_FRAMS_LIBRARY="/Users/kacperdobek/Documents/Studia/Magisterskie/Semester1/BIAM/framstics/Framsticks50rc29"

# evolution with niching
python -m evolalg.run_frams_niching  -path $DIR_WITH_FRAMS_LIBRARY \
       -sim "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim" \
       -opt COGpath -genformat 1 -dissim 1 -fit knn_niching -archive 50 \
       -fitness_set_negative_to_zero  -max_numparts 15 -max_numneurons 15 \
       -max_numjoints 30 -max_numconnections 30  -max_numgenochars 10000 \
       -popsize 30 -generations 50 -normalize none -hof_size 1 \
       -hof_savefile HoF-niching.gen \
       -log_savefile log-niching.pkl