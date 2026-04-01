################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2025-05-UltraLowDilutions/DDM02/mzML/"

sigOSW=../../bin/sif/2024-12-13-OSW-TSV-Lib.sif
sigProphet="../../bin/sif/2025-09-18-pyprophet.sif"

checkCreateFolder osw
irtPth="../../development/2025-08-22-Another-Try-PeptDeepNoMods-Determine-Optimal-Ext-Window/formattedLib/"
lib=../PeptDeep-NoMods-In-Silico-Library-Generation/2025-06-10-in-silico-lib-no-mods_fix_mods_filtered_6Frags_decoys_filtered.tsv.zst

### Run OSW Workflow ####
for mzml in $(ls ../${inputFolder}/*) 
do
	if [[ "$mzml" == *"PyDIA_R2024"* ]]
	then
		continue
	fi

	if [[ "$mzml" == *"_0pg"* ]]
	then
		continue
	fi


	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../" 
	fromMainMzML="../../" # for mzML one ../ already included in loop

	dilution=${output%pg_5x3_PyDIA*}
	dilution=${dilution#*02DDM_}

	irtLin=${irtPth}/2025-07-25-${dilution}pg-precs-for-linIrt-PeptDeepNoModsLib.tsv
	irtNonLin=${irtPth}/2025-07-25-${dilution}pg-precs-for-nonLinIrt-PeptDeepNoModsLib.tsv

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 500"

	#checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_tsv.sh ${fromMainMzML}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi
	cd ..

	# only 5000 signal has enough for XGBoost
	if [[ ${dilution} == 5000 ]]
	then
		checkCreateFolder pyprophet_LDA_XGB
		#Run Pyprophet 
		if [[ -d ../oswOut/${output}.oswpq ]]
		then
			checkAndRunSbatch ${output}_lib.tsv ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=LDA_XGBoost --ss_num_iter 3 --xeval_fraction 0.8" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
		fi
		cd ..
	fi

	#Run Pyprophet SVM
	checkCreateFolder pyprophet_SVM

	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		#checkAndRunSbatch ${output}_lib.tsv ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM --ss_scale_features --autotune" -s ${fromMain}/${sigProphet} 
		checkAndRunSbatch ${output}_lib.tsv ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM --ss_scale_features" -s ${fromMain}/${sigProphet} 
	fi
	cd ..

	cd ..


done
