################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-06-26-K562-diaPASEF/"

m1=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_1_Slot1-5_1_1330_6-28-2021.mzML
m2=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_2_Slot1-5_1_1331_6-28-2021.mzML
m3=${inputFolder}/mzML/Rost_DIApy3_SP2um_90min_250ngK562_100nL_3_Slot1-5_1_1332_6-28-2021.mzML

irtLin=formattedLib/2025-03-06-linear-irt.tsv
irtNonLin=formattedLib/2025-03-06-nonLin-iRT.tsv
lib=formattedLib/easypqp_lib_openswath_osw_6Frags_decoys.pqp
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"


########### RUN THE LIBRARY GENERATION ON AN INTERACTIVE NODE ################
checkCreateFolder formattedLib
libPth="../K562-GPF-diaTracer/"
fromMain="../"
baseLib=library.tsv

###########################################
# Run OpenSwathAssayGenerator
##########################################

module load apptainer
checkAndRun ${baseLib} cp ${fromMain}/${libPth}/${baseLib} ${baseLib}
checkAndRun ${baseLib/.tsv/_osw_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_osw_6Frags.tsv}

##################################
# Run OpenSwathDecoyGenerator
#################################
checkAndRun ${baseLib/.tsv/_osw_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_osw_6Frags.tsv} -out ${baseLib/.tsv/_osw_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

##################################
# Convert to .pqp
#################################
checkAndRun ${baseLib/.tsv/_osw_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_osw_6Frags_decoys.tsv} -out ${baseLib/.tsv/_osw_6Frags_decoys.pqp}


###############################
## Create iRT Files ##########
##############################
irtPth="../K562-Exp-Lib-Analysis/formattedLib"
irtLin=${irtPth}/2025-03-06-linear-irt.tsv
irtNonLin=${irtPth}/2025-03-06-nonLin-iRT.tsv
module load scipy-stack

checkAndRun 2025-03-06-linear-irt-for-diaTracer.tsv python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLin} ${baseLib/.tsv/_osw_6Frags.tsv} 2025-03-06-linear-irt-for-diaTracer.tsv
checkAndRun 2025-03-06-nonlinear-irt-for-diaTracer.tsv python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLin} ${baseLib/.tsv/_osw_6Frags.tsv} 2025-03-06-nonlinear-irt-for-diaTracer.tsv

cd .. 

checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $m1 $m2 $m3 
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${fromMain}/formattedLib/library_osw_6Frags_decoys.pqp ${fromMain}/formattedLib/2025-03-06-linear-irt-for-diaTracer.tsv ${fromMain}/formattedLib/2025-03-06-nonlinear-irt-for-diaTracer.tsv ${output} False ${fromMain}/${sigOSW} $additionalParam

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
