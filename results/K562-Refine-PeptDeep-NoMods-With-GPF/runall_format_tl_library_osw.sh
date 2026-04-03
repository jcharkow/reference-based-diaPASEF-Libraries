#!/bin/bash

# This script uses an .hdf file and converts it into a format for usage with DIA-NN. Should run this script on Mars
set -e
scripts="../../src"
libName=osw_tl/2025-07-14-PeptDeepNoMods-TL-On-GPF-OSW.hdf 
proteinRef=../../results/PeptDeep-NoMods-In-Silico-Library-Generation/2025-06-10-in-silico-lib-no-mods_fix_mods.tsv

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python" 

source ../../src/run_helper.sh


if [[ ! -f ${libName/.hdf/_fix_mods_filtered_appendProts.tsv} ]]
then
	checkAndRun /tmp/$(basename ${libName}) cp ${libName} /tmp
	checkAndRun /tmp/$(basename ${proteinRef}) cp ${proteinRef} /tmp
	cp ${scripts}/createTSVLib.py /tmp
	cp ${scripts}/fixMods.py /tmp
	cp ${scripts}/filterTSVLib.py /tmp
	pushd .
	cd /tmp
	checkAndRun $(basename ${libName/.hdf/.tsv}) ${PYTHON_PATH} createTSVLib.py $(basename ${libName})
	checkAndRun $(basename ${libName/.hdf/_fix_mods.tsv}) ${PYTHON_PATH} fixMods.py $(basename ${libName/.hdf/.tsv})
	checkAndRun $(basename ${libName/.hdf/_fix_mods_filtered.tsv}) ${PYTHON_PATH2} filterTSVLib.py $(basename ${libName/.hdf/_fix_mods.tsv}) -v # filter out those with less than 12 fragment ions
	checkAndRun $(basename ${libName/.hdf/_fix_mods_filtered_appendProts.tsv}) ${PYTHON_PATH2} appendProteins.py $(basename ${libName/.hdf/_fix_mods_filtered.tsv}) $(basename ${proteinRef})

	popd 
	checkAndRun ${libName/.hdf/.tsv} cp /tmp/$(basename ${libName/.hdf/.tsv}) ${libName/.hdf/.tsv}
	checkAndRun ${libName/.hdf/_fix_mods.tsv} cp /tmp/$(basename ${libName/.hdf/_fix_mods.tsv}) ${libName/.hdf/_fix_mods.tsv}
	checkAndRun ${libName/.hdf/_fix_mods_filtered.tsv} cp /tmp/$(basename ${libName/.hdf/_fix_mods_filtered.tsv}) ${libName/.hdf/_fix_mods_filtered.tsv}
	checkAndRun ${libName/.hdf/_fix_mods_filtered_appendProts.tsv} cp /tmp/$(basename ${libName/.hdf/_fix_mods_filtered_appendProts.tsv}) ${libName/.hdf/_fix_mods_filtered_appendProts.tsv}

fi

sigPath=../../bin/sif/2025-04-28-lowMemLibGen.sif

###########################################
# Run OpenSwathAssayGenerator and Decoy Generator
##########################################
lib=${libName/.hdf/_fix_mods_filtered_appendProts.tsv}
checkAndRun ${lib/.tsv/_6Frags.tsv} singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathAssayGenerator -in ${lib} -out ${lib/.tsv/_6Frags.tsv} -min_transitions 6 -max_transitions 6

checkAndRun ${lib/.tsv/_6Frags_decoys.tsv} singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathDecoyGenerator -in ${lib/.tsv/_6Frags.tsv} -out ${lib/.tsv/_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse" -batchSize 10000000 -min_decoy_fraction 0.2

### create iRT Files
irtLinOrig=../PeptDeep-NoMods-In-Silico-Library-Generation/2025-05-23-linear-irt.tsv
irtNonLinOrig=../PeptDeep-NoMods-In-Silico-Library-Generation/2025-03-06-nonlinear-irt-in-silico.tsv

irtLin=$(basename ${irtLinOrig})
irtNonLin=$(basename ${irtNonLinOrig})

scripts2=../PeptDeep-NoMods-In-Silico-Library-Generation/scripts/
checkAndRun osw_tl/${irtLin} ${PYTHON_PATH2} ${scripts2}/change_irt_space.py ${irtLinOrig} ${lib/.tsv/_6Frags.tsv} osw_tl/${irtLin}
checkAndRun osw_tl/${irtNonLin} ${PYTHON_PATH2} ${scripts2}/change_irt_space.py ${irtNonLinOrig} ${lib/.tsv/_6Frags.tsv} osw_tl/${irtNonLin}
