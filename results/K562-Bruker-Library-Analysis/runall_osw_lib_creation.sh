#!/bin/bash


# ensure in peptdeep environment
# First run 2024-11-28-Create-In-Silico-Lib.ipynb creates 2024-11-28-in-silico-lib.hdf
set -e
scripts="./scripts"
libPth="../../data/BrukerLibrary/"
libName="_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv"

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"

source ../../src/run_helper.sh

### create new iRT files in the new space
irtPth="../K562-Exp-Lib-Analysis/formattedLib"
irtLin=${irtPth}/2025-05-23-linear-irt.tsv
irtNonLin=${irtPth}/2025-03-06-nonLin-iRT.tsv
fromMain="../"

checkCreateFolder formatted
checkAndRun ${libName} cp ${fromMain}/${libPth}/${libName} ${libName}
checkAndRun ${libName/.tsv/_6Frags_decoys.pqp} ${fromMain}/${scripts}/run_library_generation_sig_var_frags_mars.sh ${libName}

checkAndRun 2025-05-23-linear-irt-in-silico.tsv ${PYTHON_PATH2} ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLin} ${libName} 2025-05-23-linear-irt-in-silico.tsv 
checkAndRun 2025-03-06-nonlinear-irt-in-silico.tsv ${PYTHON_PATH2} ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLin} ${libName} 2025-03-06-nonlinear-irt-in-silico.tsv 


