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

libPth=../2025-08-11-Create-OSW-TL-PeptDeep-Lib-Many-Frags/osw_tl
irtLin=${libPth}/2025-05-23-linear-irt.tsv
irtNonLin=${libPth}/2025-03-06-nonlinear-irt-in-silico.tsv
lib=${libPth}/2025-08-12-PeptDeepNoMods-TL-XtraFrags-On-GPF-OSW_fix_mods_filtered_appendProts_6Frags_decoys.tsv.zst
sigOSW=../../bin/sif/2024-12-13-OSW-TSV-Lib.sif
sigProphet="../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"

checkCreateFolder osw_tl
### Run OSW Workflow ####
for mzml in $m1 $m2 $m3 
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 800"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	# Convert OSW File to .oswpq
	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi
	cd ..

	
	#Run Pyprophet scoring
	checkCreateFolder pyprophet_XGB

	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ..
	#Run Pyprophet scoring
	checkCreateFolder pyprophet_SVM

	if [[ -d ../oswOut/${output}.oswpq ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_parquet.sh -f ../oswOut/${output}.oswpq -a "--classifier=SVM" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ../..

done

cd ..
