################
## Runall OSW ONLY FILTER ##
################
#
# here run with the GPF library constructed by only filtering (no RT/IM/Intensity calibration)
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-06-26-K562-diaPASEF/"

m1=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.mzML
m2=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.mzML
m3=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.mzML

libPth=../K562-Refine-Exp-Lib-With-GPF/osw/

lib=${libPth}/2025-06-02-OSW-GPF-Lib-Only-Filter.tsv
irtLin=${libPth}/2025-06-02-LiniRT-Refine-GPF-onlyFilter.tsv
irtNonLin=${libPth}/2025-06-02-nonLinIrt-Refine-GPF-onlyFilter.tsv

sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
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
checkAndRun ${baseLib/.tsv/_osw_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_osw_6Frags.tsv} -min_transitions 6 -max_transitions 6

##################################
# Run OpenSwathDecoyGenerator
#################################
checkAndRun ${baseLib/.tsv/_osw_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_osw_6Frags.tsv} -out ${baseLib/.tsv/_osw_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

##################################
# Convert to .pqp
#################################
checkAndRun ${baseLib/.tsv/_osw_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_osw_6Frags_decoys.tsv} -out ${baseLib/.tsv/_osw_6Frags_decoys.pqp}

cd ..

lib=formattedLib_osw_onlyFilter/${baseLib/.tsv/_osw_6Frags_decoys.pqp}
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
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600" # no RT/IM calibration so keep at 600 and 0.06
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

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
