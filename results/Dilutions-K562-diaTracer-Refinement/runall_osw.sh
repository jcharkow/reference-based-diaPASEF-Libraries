#!/bin/bash


# This script tests my GPF protocol. First format the library and then run trhough OSW. Note that the library generation was done locally from the ../2022-10-20-K562-Fresh-OSW-Runs results.
set -e
scripts="../../src"
source ${scripts}/run_helper.sh

sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"


inputFolder="../../data/2021-03-09-Runs/mzML/"

m1=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.mzML
m5=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.mzML
m25=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.mzML
m100=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.mzML



checkCreateFolder osw

########################################### RUN OSW  ######################################################
libPth="../Dilutions-diaTracer/"
for dilution_mzml in 1 5 25
do
	mzml=$(echo ../${inputFolder}/90min-SP-30cm-2um-K562-100nL-${dilution_mzml}ng_DIA_Slot1-*.mzML)
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output

	for dilution_lib in 5 25 100
	do
		if [[ $(( dilution_lib > dilution_mzml )) == 1 ]]
		then
			checkCreateFolder ${dilution_lib}ng_lib
			irtPth="${libPth}/${dilution_lib}ng/"
			irtLin=${irtPth}/2025-01-21-${dilution_lib}ng-linIrt_for_diaTracer.tsv # note date not changed but file is new
			irtNonLin=${irtPth}/2025-01-21-${dilution_lib}ng-nonlinIrt_for_diaTracer.tsv #note data not changed but file is new

			if [[ $(( dilution_lib == 100 )) && $(( dilution_mzml == 1 )) ]] # RT calibraiton fails here
			then
				irtLin=${irtNonLin}
			fi

			fromMain="../../../../"

			# Run OSW
			checkCreateFolder oswOut
			additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
			checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${inputFolder}/${output}.mzML ${fromMain}/${libPth}/${dilution_lib}ng/library_osw_4_6Frags_decoys.pqp ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

			cd ..

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
		fi
	done
	cd ..
done
