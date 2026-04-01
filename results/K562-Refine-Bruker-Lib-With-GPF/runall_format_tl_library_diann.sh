#!/bin/bash

# This script uses an .hdf file and converts it into a format for usage with DIA-NN. Should run this script on Mars
set -e
scripts="scripts"
libName=diann_transfer_learn/2025-06-10-Bruker-Lib-Transfer-Learn-GPF-Models-DIANN.hdf

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"

source ../../src/run_helper.sh

checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLib.py ${libName}

checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixMods.py ${libName/.hdf/.tsv} 
