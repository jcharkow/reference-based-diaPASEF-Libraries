#!/bin/bash


# ensure in peptdeep environment
# First run 2024-11-28-Create-In-Silico-Lib.ipynb creates 2024-11-28-in-silico-lib.hdf
set -e
scripts="scripts"
libName=2025-06-10-in-silico-lib-no-mods.hdf

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"

source ../../src/run_helper.sh

checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLib.py ${libName} --top_k_frags 12
checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixMods.py ${libName/.hdf/.tsv} 
checkAndRun ${libName/.hdf/_fix_mods_filtered.tsv} ${PYTHON_PATH2} scripts/filterTSVLib.py ${libName/.hdf/_fix_mods.tsv} -v # filter out those with less than 12 fragment ions

# Processing for OpenSwath
checkAndRun ${libName/.hdf/_fix_mods_filtered_6Frags_decoys.tsv} scripts/run_library_generation_sig_var_frags_mars.sh ${libName/.hdf/_fix_mods_filtered.tsv} 



### create new iRT files in the new space
irtPth="../K562-Exp-Lib-Analysis/formattedLib"
irtLin=${irtPth}/2025-05-23-linear-irt.tsv
irtNonLin=${irtPth}/2025-03-06-nonLin-iRT.tsv

checkAndRun 2025-05-23-linear-irt.tsv ${PYTHON_PATH2} scripts/change_irt_space.py ${irtLin} ${libName/.hdf/_fix_mods_filtered_6Frags.tsv} 2025-05-23-linear-irt.tsv
checkAndRun 2025-03-06-nonlinear-irt-in-silico.tsv ${PYTHON_PATH2} scripts/change_irt_space.py ${irtNonLin} ${libName/.hdf/_fix_mods_filtered_6Frags.tsv} 2025-03-06-nonlinear-irt-in-silico.tsv 


