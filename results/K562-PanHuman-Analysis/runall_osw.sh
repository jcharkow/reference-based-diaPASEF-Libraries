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

sigOSW="../../bin/sif/2025-06-19-with-irt-rtExt-param.sif"
sigProphet="../../bin/sif/2025-09-18-pyprophet.sif"


############### FORMAT LIBRARY #################################
irtPth="../../results/K562-PanHuman-Analysis/formattedLib/"
irtLin="2025-05-23-linear-irt.tsv"
irtNonLin="2025-03-06-nonLin-iRT.tsv"
fromMain="../"
lib="../../results/PanHuman-Library-Creation/2025-11-27-phl004_s32_imAppended_reannotated.tsv"

####################################
### Add new Decoys OpenSWATH ######
###################################
checkCreateFolder formattedLib_osw
###########################################
# Run OpenSwathAssayGenerator
##########################################
baseLib=$(basename ${lib})
fromMain="../"
module load apptainer
checkAndRun ${baseLib} cp ${fromMain}/${lib} ${baseLib}
checkAndRun ${baseLib/.tsv/_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_6Frags.tsv} 

##################################
# Run OpenSwathDecoyGenerator
#################################
checkAndRun ${baseLib/.tsv/_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_6Frags.tsv} -out ${baseLib/.tsv/_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

##################################
# Convert to .pqp
#################################
checkAndRun ${baseLib/.tsv/_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_6Frags_decoys.tsv} -out ${baseLib/.tsv/_6Frags_decoys.pqp}

cd ..


lib=formattedLib_osw/${baseLib/.tsv/_6Frags_decoys.pqp}

### Run OSW Workflow ####
for mzml in $m1 $m2 $m3
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 1130 -irt_nonlinear_rt_extraction_window 3000"
	checkAndRunSbatch ${output}.osw ${fromMain}/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtPth}/${irtLin} ${fromMain}/${irtPth}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi
	cd ..

	#Run Pyprophet Only run SVM because we know that XGBoost leads to erronous results
        checkCreateFolder pyprophet_SVM

        if [[ -d ../oswOut/${output}.oswpq ]]
        then
                checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM --ss_scale_features" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
        fi

	cd ../..
done

cd ..
