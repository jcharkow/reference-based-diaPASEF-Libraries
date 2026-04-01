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

lib=../K562-Refine-Bruker-Lib-With-GPF/osw_tl/2025-08-14-Bruker-TL-On-GPF-OSW_fix_mods.tsv
irtLinOrig=../K562-Bruker-Library-Analysis/formatted/2025-05-23-linear-irt-in-silico.tsv
irtNonLinOrig=../K562-Bruker-Library-Analysis/formatted/2025-03-06-nonlinear-irt-in-silico.tsv
irtLin=$(basename ${irtLinOrig})
irtNonLin=$(basename ${irtNonLinOrig})

sigOSW=../../bin/sif/2024-12-13-OSW-TSV-Lib.sif
sigProphet="../../bin/sif/2025-08-12-export_lib_unscored.sif"

######################
## Format Library ####
######################
checkCreateFolder formattedLib_osw_tl
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

#########################################
## Create irt files ##
##########################################
module load scipy-stack
checkAndRun ${irtLin} python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLinOrig} ${baseLib/.tsv/_osw_6Frags.tsv} ${irtLin}
checkAndRun ${irtNonLin} python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLinOrig} ${baseLib/.tsv/_osw_6Frags.tsv} ${irtNonLin}
cd ..

lib=formattedLib_osw_tl/${baseLib/.tsv/_osw_6Frags_decoys.tsv}
checkCreateFolder osw_tl
### Run OSW Workflow ####
for mzml in $m1 $m2 $m3 
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	# adjust this narrower because should have better calibration
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_tsv_small.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/formattedLib_osw_tl/${irtLin} ${fromMain}/formattedLib_osw_tl/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	# Convert pyprophet 
	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi

	cd ..
	#Run Pyprophet 
        checkCreateFolder pyprophet_XGB

        if [[ -d ../oswOut/${output}.oswpq ]]
        then
                checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
        fi

	cd ../..
done

cd ..
