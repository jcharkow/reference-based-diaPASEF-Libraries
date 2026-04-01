#########################
### Run DIA-NN Workflow Do not filter to 6 frags#
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
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"


#############################################
lib="../../data/BrukerLibrary/_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv"
## prepare library for DIA-NN

checkCreateFolder diann
for d in $d_1ng $d_5ng $d_25ng $d_100ng
do
	checkCreateFolder $(basename -s .d ${d})
	
	# Run OSW
	fromMain="../../"

	outLib=${d%%_DIA_Slot1*}
	outLib=${outLib#*100nL-}
	outLib=2025-02-27-lib-from-${outLib}.tsv

	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info --reannotate --full-profiling --smart-profiling"

	output=$(basename -s .d ${d}) # the output file path 
	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/create_gpf_lib_diann.sh ${fromMain}/${lib} ${fromMain}/${sifDiann} ${fromMain}/${fasta} ${outLib} 1 ${fromMain}/${d} ${additionalParam}
	cd ..
done

cd ..
