################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-03-09-Runs/mzML"

m_1ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.mzML
m_5ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.mzML
m_25ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.mzML
m_100ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.mzML

irtLin=formattedLib/2025-03-06-linear-irt.tsv
irtNonLin=formattedLib/2025-03-06-nonLin-iRT.tsv
lib=formattedLib/easypqp_lib_openswath_osw_4_6Frags_decoys.pqp
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"

module load scipy-stack
########### RUN THE LIBRARY GENERATION ON AN INTERACTIVE NODE ################
for dilution in 1 5 25 100
do
	cd ${dilution}ng
	baseLib=library.tsv
	fromMain="../"
	###########################################
	# Run OpenSwathAssayGenerator
	##########################################
	module load apptainer
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_osw_4_6Frags.tsv}

	##################################
	# Run OpenSwathDecoyGenerator
	#################################
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathDecoyGenerator -in ${baseLib/.tsv/_osw_4_6Frags.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -switchKR "true" -method "pseudo-reverse"

	##################################
	# Convert to .pqp
	#################################
	checkAndRun ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_osw_4_6Frags_decoys.tsv} -out ${baseLib/.tsv/_osw_4_6Frags_decoys.pqp}


	################################
	## change iRT space ############
	################################
	### NOTE: although there are iRTs in this folder they are formatted for the experimental library and not the diaTracer library. Here have to reformat them for the diaTracer library.
	#
	irtIn=2025-01-21-${dilution}ng-linIrt.tsv
	irtOut=${irtIn/.tsv/_for_diaTracer.tsv}
	checkAndRun ${irtOut} python ${fromMain}/${scripts}/change_irt_space.py ${irtIn} ${baseLib/.tsv/_osw_4_6Frags.tsv} ${irtOut}  

	irtIn=2025-01-21-${dilution}ng-nonlinIrt.tsv
	irtOut=${irtIn/.tsv/_for_diaTracer.tsv}
	checkAndRun ${irtOut} python ${fromMain}/${scripts}/change_irt_space.py ${irtIn} ${baseLib/.tsv/_osw_4_6Frags.tsv} ${irtOut}  

	cd ..
done

checkCreateFolder osw
### Run OSW Workflow ####
for dilution in 1 5 25 100
do
	irtPth="${dilution}ng/"
	irtLin=${irtPth}/2025-01-21-${dilution}ng-linIrt_for_diaTracer.tsv 
	irtNonLin=${irtPth}/2025-01-21-${dilution}ng-nonlinIrt_for_diaTracer.tsv

	mzml=$(echo ../${inputFolder}/90min-SP-30cm-2um-K562-100nL-${dilution}ng_DIA_Slot1-*.mzML)
	echo $mzml

	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output

	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${inputFolder}/${output}.mzML ${fromMain}/${dilution}ng/library_osw_4_6Frags_decoys.pqp ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	cd ..
	#
	if [[ $dilution == 1 || $dilution == 5 ]]
	then
		checkCreateFolder pyprophet_LDA
		if [[ -f ../oswOut/${output}.osw ]]
		then
			checkAndRunSbatch ${output}.parquet ${fromMain}/run_pyprophet_ultraStrict.sh -f ../oswOut/${output}.osw -o ${output}.osw -a "--classifier=LDA --pi0_lambda 0.001 0 0" -s ${fromMain}/${sigProphet} 
		fi
		cd ../..
	else
		#Run Pyprophet 
		if [[ $dilution == 100 ]]
		then
			checkCreateFolder pyprophet_XGB

			if [[ -f ../oswOut/${output}.osw ]]
			then
				checkAndRunSbatch ${output}.parquet ${fromMain}/${scripts}/run_pyprophet.sh -f ../oswOut/${output}.osw -o ${output}.osw -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
			fi

			cd ..
		fi

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
