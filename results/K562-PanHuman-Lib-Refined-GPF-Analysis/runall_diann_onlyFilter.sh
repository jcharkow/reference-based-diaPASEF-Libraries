#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e


inputFolder="../../data/2021-06-26-K562-diaPASEF/"
d1=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.d  
d2=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.d
d3=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.d

sifDiann="../../bin/sif/../../bin/sif/2024-12-27-diann-1_9_2.sif"

sifDiann="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"


### here I created the library manually
checkCreateFolder diann_onlyFilter

# analyze with the refined library from DIA-NN
lib="../K562-Refine-PanHuman-Lib-With-GPF/2025-06-10-diann-panHuman-gpf-refined-only-filter.tsv"
for d in $d1 $d2 $d3 
do
	checkCreateFolder $(basename -s .d ${d})
	
	# Run OSW
	fromMain="../../"

	additionalParam="--verbose 1 --direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"

	output=$(basename -s .d ${d}) # the output file path 
	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann_fasta.sh ${fromMain}/${d} ${fromMain}/${lib} ${fromMain}/${fasta} ${fromMain}/${sifDiann} ${additionalParam}
	cd ..
done

cd ..
