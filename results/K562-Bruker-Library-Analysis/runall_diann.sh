#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh


inputFolder="../../data/2021-06-26-K562-diaPASEF/"
d1=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.d  
d2=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.d
d3=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.d
GPFScheme="../../data/2021-06-26-K562-GPF/GPF_sampling_scheme.tsv"

sif="../../bin/sif/2024-12-27-diann-1_9_2.sif"
lib="../../data/BrukerLibrary/_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv"
fasta="../K562-Library-Generation/param/2024-12-09-decoys-reviewed-contam-UP000005640.fas"

## for library free analyze the results individually to ensure that match between runs is not enabled.

libNew=$(basename -s .tsv ${lib})_GPF_Filtered.tsv

### Filter the library to only those overlapping with the GPF scheme 
module load scipy-stack
checkAndRun ${libNew} python ${scripts}/filterLibraryToGPFWindows.py --cycle $GPFScheme --library ${lib} --output ${libNew}

checkCreateFolder diann
for d in $d1 $d2 $d3 
do
	checkCreateFolder $(basename -s .d ${d})
	
	# Run DIA-NN
	fromMain="../../"
	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"

	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann_fasta.sh ${fromMain}/${d} ${fromMain}/${libNew} ${fromMain}/${fasta} ${fromMain}/${sif} ${additionalParam}
	#checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann.sh ${fromMain}/${d} ${fromMain}/${lib} ${fromMain}/${sif} ${additionalParam}
	cd ..
done

cd ..
