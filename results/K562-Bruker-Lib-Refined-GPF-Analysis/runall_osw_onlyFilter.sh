################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-06-26-K562-diaPASEF/"

m1=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.mzML
m2=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.mzML
m3=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.mzML

libPth=../K562-Refine-Bruker-Lib-With-GPF/osw/

lib=${libPth}/2025-07-10-osw-bruker-gpf-refined_onlyFilter.tsv
# since just filtering the library can use the original irt files
irtLin=../K562-Bruker-Library-Analysis/formatted/2025-05-23-linear-irt-in-silico.tsv
irtNonLin=../K562-Bruker-Library-Analysis/formatted/2025-03-06-nonlinear-irt-in-silico.tsv

sigOSW="../../bin/sif/2025-06-19-with-irt-rtExt-param.sif"
sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"

######################
## Format Library ####
######################
checkCreateFolder formattedLib_osw_onlyFilter
###########################################
# Run OpenSwathAssayGenerator
##########################################

baseLib=$(basename ${lib})
fromMain="../"
module load apptainer
checkAndRun ${baseLib} cp ${fromMain}/${lib} ${baseLib}
checkAndRun ${baseLib/.tsv/_osw_4_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_osw_4_6Frags.tsv} -min_transitions 4 -max_transitions 6

##################################
# Run OpenSwathDecoyGenerator
#################################
checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_osw_4_6Frags.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

##################################
# Convert to .pqp
#################################
checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp}

cd ..

lib=formattedLib_osw_onlyFilter/${baseLib/.tsv/_osw_4_6Frags_decoys.pqp}
checkCreateFolder osw_onlyFilter
### Run OSW Workflow ####
for mzml in $m1 $m2 $m3 
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	# adjust this narrower because should have better calibration
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 1580 -irt_nonlinear_rt_extraction_window 3000"

	checkAndRunSbatch ${output}.osw ${fromMain}/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtNonLin} ${fromMain}/${irtNonLin} ${output} True ${fromMain}/${sigOSW} $additionalParam

	cd ..
	#
	#Run Pyprophet 
	checkCreateFolder pyprophet_XGB

	if [[ -f ../oswOut/${output}.osw ]]
	then
		checkAndRunSbatch ${output}.parquet ${fromMain}/${scripts}/run_pyprophet.sh -f ../oswOut/${output}.osw -o ${output}.osw -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ..

	#Run Pyprophet  LDA
	checkCreateFolder pyprophet_LDA

	if [[ -f ../oswOut/${output}.osw ]]
	then
		checkAndRunSbatch ${output}.parquet ${fromMain}/${scripts}/run_pyprophet.sh -f ../oswOut/${output}.osw -o ${output}.osw -a "--classifier=LDA" -s ${fromMain}/${sigProphet} 
	fi
	cd ../..

done

cd ..
