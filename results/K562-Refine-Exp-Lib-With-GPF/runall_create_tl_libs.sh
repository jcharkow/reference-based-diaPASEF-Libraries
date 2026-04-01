#!/bin/bash


# ensure in peptdeep environment
# First run 2024-11-28-Create-In-Silico-Lib.ipynb creates 2024-11-28-in-silico-lib.hdf
set -e
scripts="scripts"

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"

#### Create OpenSWATH models
source ../../src/run_helper.sh
scripts="../../src"

checkCreateFolder osw_tl
cd ..


## In New script refine from the full library, this includes precursors that were previously filtered out due to lack of fragments 
# note need to fix library because .UniMod (with leading "." is not recognized by OpenSWATH library

python3 <<'PYCODE'
import pandas as pd

df = pd.read_csv("../K562-Library-Generation/library.tsv", sep="\t")

# Remove leading dot before (UniM) in ModifiedSequence
df['ModifiedPeptideSequence'] = df['ModifiedPeptideSequence'].str.replace(
    r'^\.\(UniM', r'(UniM', regex=True
)

df.to_csv("library_fixed.tsv", sep="\t", index=False)
PYCODE

python3 <<'PYCODE'
import pandas as pd

df = pd.read_csv("osw_xtra_frags/2025-08-15-exp-lib-refined_GPF_manyFrags_OSW.tsv", sep="\t")

# Remove leading dot before (UniM) in ModifiedSequence
df['ModifiedPeptideSequence'] = df['ModifiedPeptideSequence'].str.replace(
    r'^\.\(UniM', r'(UniM', regex=True
)

df.to_csv("osw_xtra_frags/2025-08-15-exp-lib-refined_GPF_manyFrags_OSW_fixed.tsv", sep="\t", index=False)
PYCODE


python ${scripts}/apply-TL.py --rsltsIn osw_xtra_frags/2025-08-15-exp-lib-refined_GPF_manyFrags_OSW_fixed.tsv --libIn library_fixed.tsv --libOut osw_tl/2025-08-15-Exp-TL-On-GPF-OSW.hdf --modelSuffix Exp-GPF --model osw_models/ 
libName=osw_tl/2025-08-15-Exp-TL-On-GPF-OSW.hdf

source ../../src/run_helper.sh

checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLib.py ${libName}

checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixMods.py ${libName/.hdf/.tsv} 

######################################
# Create the DIA-NN TL Library
libName=diann_transfer_learn/2025-06-11-ExpLib-Lib-Transfer-Learn-GPF-Models-DIANN.hdf
checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLibNEW.py ${libName}
checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixMods.py ${libName/.hdf/.tsv} 
