scripts="../../src"

set -e
source ${scripts}/run_helper.sh


inputFolder="../../data/2025-05-UltraLowDilutions/DDM02/"

sif="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"
lib="../../data/BrukerLibrary/_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv"

## for library free analyze the results individually to ensure that match between runs is not enabled.


inputFolder="../../data/2025-05-UltraLowDilutions/DDM02/mzML/"
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
sigProphet="../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"
lib="formatted/_ip2_ip2_data_paser_spectral_library__Bruker_Human_6Frags_decoys.pqp" 
fromMain="../"


############# MAKE THE iRTs ##########
libTargets="formatted/_ip2_ip2_data_paser_spectral_library__Bruker_Human_6Frags.tsv" 
irtPrecs_pth="../../results/diaTracer-Analysis/irtPrecs" # path to where iRT files are found, note that these are only the precursors and not the full iRT file
checkCreateFolder irts
module load scipy-stack
fromMain="../"
for irtPrecs in $(ls ${fromMain}/${irtPrecs_pth})
do
	out=$(basename ${irtPrecs/.tsv}-BrukerLib.tsv)
	checkAndRun ${out} python ${fromMain}/${scripts}/create_irt_from_precs.py ${fromMain}/${irtPrecs_pth}/${irtPrecs} ${fromMain}/${libTargets} ${out}
done
cd ..

checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $(ls ../${inputFolder}/*) 
do
	if [[ "$mzml" == *"PyDIA_R2024"* ]]
	then
		continue
	fi

	if [[ "$mzml" == *"-0pg"* ]]
	then
		continue
	fi


	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../" 
	fromMainMzML="../../" # for mzML one ../ already included in loop

	dilution=${output%pg_5x3_PyDIA*}
	dilution=${dilution#*02DDM_}

	irtPth=irts
	irtLin=${irtPth}/2025-07-25-${dilution}pg-precs-for-linIrt-BrukerLib.tsv
	irtNonLin=${irtPth}/2025-07-25-${dilution}pg-precs-for-nonLinIrt-BrukerLib.tsv

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window -1"

	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMainMzML}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi
	cd ..


	checkCreateFolder pyprophet_XGB
	#Run Pyprophet 
	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		checkAndRunSbatch ${output}_lib.tsv ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ..
	#Run Pyprophet  LDA
	checkCreateFolder pyprophet_LDA

	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		checkAndRunSbatch ${output}_lib.tsv ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=LDA" -s ${fromMain}/${sigProphet} 
	fi
	cd ../..

done

cd ..
