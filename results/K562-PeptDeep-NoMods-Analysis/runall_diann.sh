#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh


inputFolder="../../data/2021-06-26-K562-diaPASEF/"
d1=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.d  
d2=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.d
d3=${inputFolder}/d/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.d

sif="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"
lib="../PeptDeep-NoMods-In-Silico-Library-Generation/2025-06-10-in-silico-lib-no-mods_fix_mods_filtered.tsv"  #### USE THE LIBRARY THAT WAS NOT PROCCESSED BY OPENSWATH THUS HAS MANY FRAGMENT IONS
GPFScheme="../../data/2021-06-26-K562-GPF/GPF_sampling_scheme.tsv"

## for library free analyze the results individually to ensure that match between runs is not enabled.
libNew=$(basename -s .tsv ${lib})_GPF_Filtered.tsv

### **NEW** Filter the library to only those overlapping with the GPF scheme 
module load scipy-stack
checkAndRun ${libNew} python ${scripts}/filterLibraryToGPFWindows.py --cycle $GPFScheme --library ${lib} --output ${libNew}

## for library free analyze the results individually to ensure that match between runs is not enabled.
checkCreateFolder diann
for d in $d1 $d2 $d3 
do
	checkCreateFolder $(basename -s .d ${d})
	
	# Run DIA-NN
	fromMain="../../"
	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"

	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann_fasta.sh ${fromMain}/${d} ${fromMain}/${libNew} ${fromMain}/${fasta} ${fromMain}/${sif} ${additionalParam}
	cd ..
done
