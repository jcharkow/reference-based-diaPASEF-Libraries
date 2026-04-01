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


lib=../2025-11-27-PanHuman-Library-Full-New-Workflow-Prot-Annot-New-Decoys/formattedLib_osw/2025-11-27-phl004_s32_imAppended_reannotated_6Frags_decoys.pqp
sigOSW="../../bin/sif/2025-06-19-with-irt-rtExt-param.sif"
sigProphet="../../bin/sif/2025-07-11-pyprophet_createLib.sif"

checkCreateFolder osw

for dilution in 1 5 25 100
do
	irtPth="../../results/Dilutions-diaTracer/${dilution}ng/"
	# Need to change iRT Space first
	irtLin=${irtPth}/2025-01-21-${dilution}ng-linIrt.tsv # note date not changed but file is new
	irtNonLin=${irtPth}/2025-01-21-${dilution}ng-nonlinIrt.tsv #note data not changed but file is new

	fromMain="../"
	mzml=$(echo ${fromMain}/${inputFolder}/90min-SP-30cm-2um-K562-100nL-${dilution}ng_DIA_Slot1-*.mzML)

	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output

	# change iRT space 
	module load scipy-stack

	fromMain="../../"
	checkAndRun $(basename ${irtLin}) python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtLin} ${fromMain}/${lib/.pqp/.tsv} $(basename ${irtLin})
	checkAndRun $(basename ${irtNonLin}) python ${fromMain}/${scripts}/change_irt_space.py ${fromMain}/${irtNonLin} ${fromMain}/${lib/.pqp/.tsv} $(basename ${irtNonLin})
	
	# Run OSW
	checkCreateFolder oswOut

	fromMain="../../../"
	fromMainMzML="../../" # need one less level because one already included 


	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 1130 -irt_nonlinear_rt_extraction_window 3000"
	checkAndRunSbatch ${output}.osw ${fromMain}/../../development/2025-06-24-Bruker-Lib-Analysis/run_osw_tsv.sh ${fromMainMzML}/${mzml} ${fromMain}/${lib} ../$(basename ${irtLin}) ../$(basename ${irtNonLin}) ${output} True ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi

	cd ..
	#
	#Run Pyprophet and create library
	checkCreateFolder pyprophet_XGB

	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		checkAndRunSbatch ${output}_ms1ms2_report.pdf ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ..
	## Since pyprophet XGB tends to overfit and LDA is not powerful enough SVM might be the best option
	#Run Pyprophet  SVM
	checkCreateFolder pyprophet_SVM
	if [[ -d ../oswOut/${output}.oswpq ]]
		then
			checkAndRunSbatch ${output}_ms1ms2_report.pdf ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi
	
	cd ../..

done

cd ..
