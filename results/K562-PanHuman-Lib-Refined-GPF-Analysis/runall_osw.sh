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

lib=../2025-12-02-Refined-PanHuman-Lib-With-GPF-Reannotated-Lib-New-Decoys/osw/2025-11-26-osw-PHL-gpf-refined-SVM.tsv

irtLin=2025-11-26-linear-irt-NEW.tsv
irtNonLin=2025-11-26-nonlinear-irt-NEW.tsv

sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2025-09-18-pyprophet.sif"

######################
## Format Library ####
######################
checkCreateFolder formattedLib_osw
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


#########################################
## Create irt files ##
##########################################
module load scipy-stack
checkAndRun ${irtLin} python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLinOrig} ${baseLib/.tsv/_osw_4_6Frags.tsv} ${irtLin}
checkAndRun ${irtNonLin} python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLinOrig} ${baseLib/.tsv/_osw_4_6Frags.tsv} ${irtNonLin}
cd ..

lib=formattedLib_osw/${baseLib/.tsv/_osw_4_6Frags_decoys.pqp}
checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $m1 $m2 $m3 
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	# adjust this narrower because should have better calibration
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.04 -rt_extraction_window 300"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${fromMain}/formattedLib_osw/${baseLib/.tsv/_osw_4_6Frags_decoys.pqp} ${fromMain}/formattedLib_osw/${irtLin} ${fromMain}/formattedLib_osw/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam
	
	# Convert pyprophet 
	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi

	cd ..
	#Run Pyprophet 
        checkCreateFolder pyprophet_SVM

        if [[ -d ../oswOut/${output}.oswpq ]]
        then
                checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM --ss_scale_features" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
        fi
	cd ../..


done

cd ..
