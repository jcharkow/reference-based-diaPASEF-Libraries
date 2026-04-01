#!/bin/bash

# This script is adapted for creating a library on mars

##############################################
# Commandline arguments
##############################################
echo $(ls)
lib=$1
frags=$2
sigPath=../../../bin/sif/openms-executables-sif_3.2.0.sif

set -e

source ../../../src/run_helper.sh


###########################################
# Run OpenSwathAssayGenerator
##########################################
checkAndRun ${lib/.tsv/_6Frags.tsv} singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathAssayGenerator -in ${lib} -out ${lib/.tsv/_6Frags.tsv} -min_transitions 6 -max_transitions 6

##################################
# Run OpenSwathDecoyGenerator
#################################
checkAndRun ${lib/.tsv/_6Frags_decoys.tsv} singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} OpenSwathDecoyGenerator -in ${lib/.tsv/_6Frags.tsv} -out ${lib/.tsv/_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

###############################
# TargetedFileConverter 
##############################
checkAndRun ${lib/.tsv/_6Frags_decoys.pqp} singularity exec --bind $(pwd):/mnt -H /mnt ${sigPath} TargetedFileConverter -in ${lib/.tsv/_6Frags_decoys.tsv} -out ${lib/.tsv/_6Frags_decoys.pqp} 
