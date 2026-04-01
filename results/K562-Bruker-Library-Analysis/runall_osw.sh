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

sigOSW="../../bin/sif/2025-06-19-with-irt-rtExt-param.sif"
sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"


############### FORMAT LIBRARY #################################
irtPth="../../results/K562-Bruker-Library-Analysis/formatted/"
irtLin="2025-05-23-linear-irt-in-silico.tsv"
irtNonLin="2025-03-06-nonlinear-irt-in-silico.tsv"
fromMain="../"
lib="_ip2_ip2_data_paser_spectral_library__Bruker_Human_6Frags_decoys.pqp"

### Run OSW Workflow ####
for mzml in $m1 $m2 $m3
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 1580 -irt_nonlinear_rt_extraction_window 3000"
	checkAndRunSbatch ${output}.osw ${fromMain}/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${irtPth}/${lib} ${fromMain}/${irtPth}/${irtLin} ${fromMain}/${irtPth}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	cd ..
	#
	#Run Pyprophet 
	checkCreateFolder pyprophet_XGB

	if [[ -f ../oswOut/${output}.osw ]]
	then
		checkAndRunSbatch ${output}.parquet ${fromMain}/${scripts}/run_pyprophet.sh -f ../oswOut/${output}.osw -o ${output}.osw -a "--classifier=XGBoost --ss_main_score=var_dotprod_score" -s ${fromMain}/${sigProphet} # Note if do not fix the ss_main_score than we get failure in running
	fi

	cd ../..
done

cd ..
