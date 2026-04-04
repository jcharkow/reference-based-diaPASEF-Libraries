#!/bin/bash

# First step is to append IM values using the alphapeptdeep model. This is done on the boltzmann cluster

# Next I want to format the library for usage with DIA-NN

source ../../src/run_helper.sh

PYTHON_PATH="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"
sigPath=../../bin/sif/2025-04-28-lowMemLibGen.sif

set -e

###########################################
# Run OpenSwathAssayGenerator
##########################################
checkAndRun phl004_s32_imAppended.tsv cp phl004_s32_imAppended.csv phl004_s32_imAppended.tsv 
checkAndRun phl004_s32_imAppended_fixed.tsv singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathAssayGenerator -in phl004_s32_imAppended.tsv  -out phl004_s32_imAppended_fixed.tsv  -min_transitions 6 -max_transitions 6

checkAndRun phl004_s32_imAppended_fixed_diann.tsv ${PYTHON_PATH} ../../src/format_library_diann.py phl004_s32_imAppended_fixed.tsv phl004_s32_imAppended_fixed_diann.tsv


################################
# Format Library for OpenSWATH #
# ##############################

# Since OpenSWATH assay generator automatically removes decoys, we need to split the file, then run OpenSwathAssayGenerator and then combine

# Remove extension for base name
input=phl004_s32_imAppended.csv
base="${input%.csv}"

# split into targets and decoys
if [[ ! -f ${base}_decoy0.tsv ]] || [[ ! -f ${base}_decoy1.tsv ]]
then
	echo Spltting ${base} ...

	${PYTHON_PATH} - <<EOF
import pandas as pd

input_file = "$input"
base = "$base"

df = pd.read_csv(input_file, sep='\t')

if 'decoy' not in df.columns:
    raise ValueError("Column 'decoy' not found in file")

# Split and set decoy=0 in both outputs
df0 = df[df['decoy'] == 0].copy()
df1 = df[df['decoy'] == 1].copy()
df1['decoy'] = 0  # Set to 0

df0.to_csv(f"{base}_decoy0.tsv", sep='\t', index=False)
df1.to_csv(f"{base}_decoy1.tsv", sep='\t', index=False)
EOF
fi

################## Run OpenSwathAssayGenerator on both files #################
checkAndRun ${base}_decoy0_fixed.tsv singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathAssayGenerator -in ${base}_decoy0.tsv  -out ${base}_decoy0_fixed.tsv  -min_transitions 6 -max_transitions 6

checkAndRun ${base}_decoy1_fixed.tsv singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathAssayGenerator -in ${base}_decoy1.tsv  -out ${base}_decoy1_fixed.tsv  -min_transitions 6 -max_transitions 6

##### Combine Files back ##############
if [[ -f ${base}_decoy0_fixed.tsv ]] && [[ -f ${base}_decoy1_fixed.tsv ]]
then
	if [[ ! -f ${base}_fixed_with_decoys.tsv ]]
	then
		echo Combinning ${base} ...

		${PYTHON_PATH} - <<EOF
import pandas as pd

base = "$base"
df_0 = pd.read_csv(f"{base}_decoy0_fixed.tsv", sep='\t')
df_1 = pd.read_csv(f"{base}_decoy1_fixed.tsv", sep='\t')

# Mark decoys
df_1['Decoy'] = 1 # decoy column renamed to Decoy

# Combine
combined = pd.concat([df_0, df_1], ignore_index=True)

# Save
combined.to_csv(f"{base}_fixed_with_decoys.tsv", sep='\t', index=False)
EOF

fi
fi

sigPath=../../bin/sif/openms-executables-sif_3.2.0.sif
checkAndRun ${base}_fixed_with_decoys.pqp singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} TargetedFileConverter -in ${base}_fixed_with_decoys.tsv  -out ${base}_fixed_with_decoys.pqp 
