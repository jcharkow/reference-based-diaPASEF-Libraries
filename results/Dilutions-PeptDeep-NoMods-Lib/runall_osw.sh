################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-03-09-Runs/mzML/"


m_1ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.mzML    
m_5ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.mzML
m_25ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.mzML
m_100ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.mzML  

libPth=../../results/PeptDeep-NoMods-In-Silico-Library-Generation/
lib=${libPth}/2025-06-10-in-silico-lib-no-mods_fix_mods_filtered_6Frags_decoys_filtered.tsv.zst
sigOSW=../../bin/sif/2024-12-13-OSW-TSV-Lib.sif
sigProphet="../../bin/sif/2025-07-11-pyprophet_createLib.sif"
sigProphet2="../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"
sifProphet3="../../bin/sif/2025-08-12-export_lib_unscored.sif"
sigProphetSqMass="../../bin/sif/2025-08-19-pyprophet-export-xics.sif"

module load apptainer

PYTHON_PATH=/home/jsc718/jos_jup/bin/python

checkCreateFolder osw

for dilution in 1 5 25 100
do
	irtPth="../Dilutions-diaTracer/${dilution}ng/"
	# Need to change iRT Space first
	irtLin=${irtPth}/2025-01-21-${dilution}ng-linIrt.tsv # note date not changed but file is new
	irtNonLin=${irtPth}/2025-01-21-${dilution}ng-nonlinIrt.tsv #note data not changed but file is new

	fromMain="../"
	mzml=$(echo ${fromMain}/${inputFolder}/90min-SP-30cm-2um-K562-100nL-${dilution}ng_DIA_Slot1-*.mzML)

	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output

	fromMain="../../"
	checkAndRun $(basename ${irtLin}) ${PYTHON_PATH} ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLin} ${fromMain}/${lib/_decoys_filtered.tsv.zst/.tsv.zst} $(basename ${irtLin})
	checkAndRun $(basename ${irtNonLin}) ${PYTHON_PATH} ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLin} ${fromMain}/${lib/_decoys_filtered.tsv.zst/.tsv.zst} $(basename ${irtNonLin})
	
	# Run OSW
	checkCreateFolder oswOut

	fromMain="../../../"
	fromMainMzML="../../" # need one less level because one already included 
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 800"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_tsv.sh ${fromMainMzML}/${mzml} ${fromMain}/${lib} ../$(basename ${irtLin}) ../$(basename ${irtNonLin}) ${output} True ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
		checkAndRunSbatch ${output}_XIC.parquet ${fromMain}/${scripts}/run_pyprophet_export_sqmass.sh -f ${output}.sqMass -p ${output}.osw -s ${fromMain}/${sigProphetSqMass}
	fi

	cd ..
	#
		
	#Run Pyprophet scoring
	if [[ ${dilution} == 25 || ${dilution} == 100 ]]
	then
		checkCreateFolder pyprophet_XGB

		if [[ -d ../oswOut/${output}.oswpq ]]
		then
			checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
		fi
	cd .. 
	fi
		
	checkCreateFolder pyprophet_LDA

	#if [[ -d ../oswOut/${output}.oswpq ]]
	#then
	#	checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=LDA" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running

	#fi

	cd ..

	if [[ ${dilution} == 5 || ${dilution} == 25 || ${dilution} == 100 ]]
	then
		checkCreateFolder pyprophet_LDA_XGBoost

		if [[ -d ../oswOut/${output}.oswpq ]]
		then
			checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=LDA_XGBoost" -s ${fromMain}/${sigProphet2} # to try and prevent pi0 crashes
		fi

	cd ..
	fi

	cd ../..

done

cd ..
