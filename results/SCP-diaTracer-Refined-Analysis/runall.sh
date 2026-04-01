#!/bin/bash

# This script performs refined library analysis with DIA-NN 

set -e

python runall_diann.py "sbatch"
#
source ../../src/run_helper.sh

##### create extra iRT files for OpenSWATH
irtLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-100pg-precs-for-linIrt.tsv
irtNonLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-100pg-precs-for-nonLinIrt.tsv
irtOutLin=../diaTracer-Analysis/osw_masterLib/2500pg/irts/2025-07-25-100pg-linIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv 
irtOutNonLin=../diaTracer-Analysis/osw_masterLib/2500pg/irts/2025-07-25-100pg-nonLinIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv 
lib=../diaTracer-Analysis/HeLa02DDM_2500pg_5x3_PyDIA_3_S1-D6_1_1656/library_osw_6Frags.tsv
checkAndRun ${irtOutLin} python ../../src/create_irt_from_precs.py ${irtLinPrecs} ${lib} ${irtOutLin}
checkAndRun ${irtOutNonLin} python ../../src/create_irt_from_precs.py ${irtNonLinPrecs} ${lib} ${irtOutNonLin}


irtOutLin=../diaTracer-Analysis/osw_masterLib/500pg/irts/2025-07-25-100pg-linIrt-diaTracerLib_refined_for_500pg_rep_3_lib.tsv 
irtOutNonLin=../diaTracer-Analysis/osw_masterLib/500pg/irts/2025-07-25-100pg-nonLinIrt-diaTracerLib_refined_for_500pg_rep_3_lib.tsv 
lib=../diaTracer-Analysis/HeLa02DDM_500pg_5x3_PyDIA_3_S1-C12_1_1644/library_osw_6Frags.tsv
checkAndRun ${irtOutLin} python ../../src/create_irt_from_precs.py ${irtLinPrecs} ${lib} ${irtOutLin}
checkAndRun ${irtOutNonLin} python ../../src/create_irt_from_precs.py ${irtNonLinPrecs} ${lib} ${irtOutNonLin}

irtLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-250pg-precs-for-linIrt.tsv
irtNonLinPrecs=../diaTracer-Analysis/irtPrecs/2025-07-25-250pg-precs-for-nonLinIrt.tsv
irtOutLin=../diaTracer-Analysis/osw_masterLib/2500pg/irts/2025-07-25-250pg-linIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv 
irtOutNonLin=../diaTracer-Analysis/osw_masterLib/2500pg/irts/2025-07-25-250pg-nonLinIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv 
lib=../diaTracer-Analysis/HeLa02DDM_2500pg_5x3_PyDIA_3_S1-D6_1_1656/library_osw_6Frags.tsv
checkAndRun ${irtOutLin} python ../../src/create_irt_from_precs.py ${irtLinPrecs} ${lib} ${irtOutLin}
checkAndRun ${irtOutNonLin} python ../../src/create_irt_from_precs.py ${irtNonLinPrecs} ${lib} ${irtOutNonLin}



python runall_osw.py "sbatch"



