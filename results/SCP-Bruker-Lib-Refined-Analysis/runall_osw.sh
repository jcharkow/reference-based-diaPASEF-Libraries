#!/bin/bash

# This script performs refined library analysis with DIA-NN 

set -e

module load scipy-stack
module load apptainer
source ../../src/run_helper.sh

# create manual iRTs for files that failed
#irtLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-250pg-precs-for-linIrt.tsv
#irtNonLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-250pg-precs-for-nonLinIrt.tsv

irtLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-100pg-precs-for-linIrt.tsv
irtNonLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-100pg-precs-for-nonLinIrt.tsv
irtOutLin=osw/irts/2025-07-25-100pg-linIrt-BrukerLib_refined_for_2500pg_rep_1_lib.tsv 
irtOutNonLin=osw/irts/2025-07-25-100pg-nonLinIrt-BrukerLib_refined_for_2500pg_rep_1_lib.tsv 
checkAndRun ${irtOutLin} python ../../src/create_irt_from_precs.py ${irtLinPrecs} osw/pqp_libraries/HeLa02DDM_2500pg_5x3_PyDIA_1_S1-D4_1_1654_osw_4_6Frags.tsv ${irtOutLin}
checkAndRun ${irtOutNonLin} python ../../src/create_irt_from_precs.py ${irtNonLinPrecs} osw/pqp_libraries/HeLa02DDM_2500pg_5x3_PyDIA_1_S1-D4_1_1654_osw_4_6Frags.tsv ${irtOutNonLin}

python runall_osw.py "sbatch" "regular"
