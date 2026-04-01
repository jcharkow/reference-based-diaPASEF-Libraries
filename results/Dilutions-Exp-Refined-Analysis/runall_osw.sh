#!/bin/bash


# This script tests my GPF protocol. First format the library and then run trhough OSW. Note that the library generation was done locally from the ../2022-10-20-K562-Fresh-OSW-Runs results.
set -e
scripts="../../src"
source ${scripts}/run_helper.sh

sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2025-07-11-pyprophet_createLib.sif"
sifProphet3="../../bin/sif/2025-08-12-export_lib_unscored.sif"


########### FUNCTION #################
function run_osw_pyprophet() { 
	lib=$1
	mzml=$2
	linirt=$3
	nonlinirt=$4

	dilution_lib=${lib%ng_DIA_Slot*lib_osw_4_6Frags_decoys.pqp}
	dilution_lib=${dilution_lib#*100nL-}

	dilution_mzml=${mzml%ng_DIA_Slot1*}
	dilution_mzml=${dilution_mzml#*100nL-}

	folder=${dilution_mzml}ng_${dilution_lib}_lib
	output=$(basename -s .mzML ${mzml})
	checkCreateFolder ${folder}
	checkCreateFolder oswOut
	
	# Run OSW
	fromMain="../../../../"


	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
	if [[ ${dilution_lib} == 100 && ${dilution_mzml} == 1 ]]
	then
		checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${lib} ${nonlinirt} ${nonlinirt} ${output} True ${fromMain}/${sigOSW} $additionalParam
	else
		checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${lib} ${linirt} ${nonlinirt} ${output} True ${fromMain}/${sigOSW} $additionalParam
	fi

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
		if [[ -d ${output}.oswpq ]]
		then
			checkAndRun ${output}_nativeRT.tsv apptainer exec ${fromMain}/${sifProphet3} pyprophet export library --in ${output}.oswpq --out ${output}_nativeRT.tsv --rt_unit RT
		fi
        fi

	cd ../..
}



inputFolder="../../data/2021-03-09-Runs/mzML/"

m1=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.mzML
m5=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.mzML
m25=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.mzML
m100=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.mzML

#############
## Format Libraries
##################

checkCreateFolder osw
checkCreateFolder osw_formattedLib

libPth=../Dilutions-K562-Exp-Lib/osw
fromMain="../.."
for lib in $(find ${fromMain}/${libPth} -wholename "*/pyprophet_XGB/*_lib.tsv")
do

	###########################################
	# Run OpenSwathAssayGenerator
	##########################################

	module load apptainer
	baseLib=$(basename ${lib})
	checkAndRun ${baseLib} cp ${lib} ${baseLib}
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_osw_4_6Frags.tsv} -min_transitions 4 -max_transitions 6

	##################################
	# Run OpenSwathDecoyGenerator
	#################################
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_osw_4_6Frags.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

	##################################
	# Convert to .pqp
	#################################
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp}

done

# change irt space 
module load scipy-stack
for irt in $(find ${fromMain}/${libPth} -wholename "*/2025-03-07*.tsv")
do
	echo ${irt}
	if [[ ${irt} == *"2025-03-07-1ng"* ]]
	then
		continue
	else
		dilution_irt=${irt%ng*}
		dilution_irt=-${dilution_irt#*2025-03-07-}ng
		irtOut=$(basename ${irt})
		libPth=$(find . -name "90min-SP-30cm*${dilution_irt}*_osw_4_6Frags.tsv")
		echo lib pth is ${libPth}
		checkAndRun ${irtOut} python ${fromMain}/${scripts}/change_irt_space.py ${irt} ${libPth} ${irtOut}  
	fi
done
cd ..

########################################### RUN OSW  ######################################################
echo running osw
for m in $m1 $m5 $m25 $m100
do
	### get the dilution number 
	dilution_mzml=${m%ng_DIA_Slot1*} # note lib dates not updated but generated new
	dilution_mzml=${dilution_mzml#*100nL-}
	checkCreateFolder ${dilution_mzml}ng
	for lib in $(ls ../osw_formattedLib)
	do
		if [[ ${lib} == *_decoys.pqp ]]
		then
			dilution_lib=${lib%ng_DIA_Slot*lib_osw_4_6Frags_decoys.pqp}
			dilution_lib=${dilution_lib#*100nL-}
			echo dilution lib is ${dilution_lib}
			if [[ $(( dilution_mzml < dilution_lib )) == 1 ]]
			then
				fromMain="../../.."
				libPth=${fromMain}/osw_formattedLib
				run_osw_pyprophet ${libPth}/${lib} ${m} ${libPth}/2025-03-07-${dilution_lib}ng-LiniRT.tsv ${libPth}/2025-03-07-${dilution_lib}ng-nonLinIrt.tsv	
			fi
		fi
	done
	cd ..
done
