#!/bin/bash 
#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e


inputFolder="../../data/2021-03-09-Runs/d"

d_1ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.d
d_5ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.d
d_25ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.d
d_100ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.d

sifDiann="../../bin/sif/2024-12-27-diann-1_9_2.sif"
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
fasta="../K562-Library-Generation/param/2024-12-09-decoys-reviewed-contam-UP000005640.fas"

checkCreateFolder diann

fromMain="../"
######################
### Analyze Library ##
######################
for d in $d_1ng $d_5ng $d_25ng $d_100ng
do
	### get the dilution number 
	dilution=${d%ng_DIA_Slot1*}
	dilution=${dilution#*100nL-}
	checkCreateFolder ${dilution}ng
	fromMain="../../"
	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"
	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann_fasta.sh ${fromMain}/${d} ${fromMain}/${dilution}ng/library.tsv ${fromMain}/${fasta} ${fromMain}/${sifDiann} ${additionalParam}
	cd ..
done
cd ..
