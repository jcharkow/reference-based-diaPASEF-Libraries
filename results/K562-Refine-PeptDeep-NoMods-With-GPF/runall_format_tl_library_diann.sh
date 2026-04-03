#!/bin/bash

# This script uses an .hdf file and converts it into a format for usage with DIA-NN. Should run this script on Mars
set -e
scripts="../../src"

 /banana/rostlab/jcharkow/.conda/envs/peptdeep/bin/python apply-TL.py --rsltsIn 2025-06-18-peptdeep-nomods-gpf-refined-diann.tsv --libIn ../PeptDeep-NoMods-In-Silico-Library-Generation/2025-06-10-in-silico-lib-no-mods.hdf --libOut diann_tl/2025-06-21-PeptDeepNoMods-TL-On-GPF-DIANN.hdf --model diann_models --modelSuffix peptDeepNoMods_DIANN_GPF_refined

libName1=diann_tl/2025-06-21-PeptDeepNoMods-TL-On-GPF-DIANN.hdf

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python" 

source ../../src/run_helper.sh

for libName in ${libName1}
do
	if [[ ! -f ${libName/.hdf/_fix_mods_filtered.tsv} ]]
	then
		checkAndRun /tmp/$(basename ${libName}) cp ${libName} /tmp
		cp ${scripts}/createTSVLib.py /tmp
		cp ${scripts}/fixMods.py /tmp
		cp ${scripts}/filterTSVLib.py /tmp
		pushd .
		cd /tmp
		checkAndRun $(basename ${libName/.hdf/.tsv}) ${PYTHON_PATH} createTSVLib.py $(basename ${libName})
		checkAndRun $(basename ${libName/.hdf/_fix_mods.tsv}) ${PYTHON_PATH} fixMods.py $(basename ${libName/.hdf/.tsv})
		checkAndRun $(basename ${libName/.hdf/_fix_mods_filtered.tsv}) ${PYTHON_PATH2} filterTSVLib.py $(basename ${libName/.hdf/_fix_mods.tsv}) -v # filter out those with less than 12 fragment ions
		popd 
		checkAndRun ${libName/.hdf/.tsv} cp /tmp/$(basename ${libName/.hdf/.tsv}) ${libName/.hdf/.tsv}
		checkAndRun ${libName/.hdf/_fix_mods.tsv} cp /tmp/$(basename ${libName/.hdf/_fix_mods.tsv}) ${libName/.hdf/_fix_mods.tsv}
		checkAndRun ${libName/.hdf/_fix_mods_filtered.tsv} cp /tmp/$(basename ${libName/.hdf/_fix_mods_filtered.tsv}) ${libName/.hdf/_fix_mods_filtered.tsv}
	fi
done
