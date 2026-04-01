#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh


inputFolder="../../data/2025-05-UltraLowDilutions/DDM02/"

sif="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"
lib="../../data/BrukerLibrary/_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv"

## for library free analyze the results individually to ensure that match between runs is not enabled.
checkCreateFolder diann
for d in $(ls ../${inputFolder}) 
do
	echo ${d}
	checkCreateFolder $(basename -s .d ${d})
	
	# Run DIA-NN
	fromMain="../../"
	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"

	dilution=${d%%pg*}
	dilution=${dilution#*02DDM_}

	rep=$(basename ${d})
	rep=${rep%_S*}
	rep=${rep##*_PyDIA_}
	outLib=2025-06-11-lib-from-${dilution}ng-rep${rep}.parquet
	echo outLib ${outLib}

	additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info --reannotate --full-profiling --smart-profiling"

	output=$(basename -s .d ${d}) # the output file path 
	checkAndRunSbatch report.tsv ${fromMain}/${scripts}/create_gpf_lib_diann.sh ${fromMain}/${lib} ${fromMain}/${sif} ${fromMain}/${fasta} ${outLib} 1 ${fromMain}/${inputFolder}/${d} ${additionalParam}
	cd ..
done
