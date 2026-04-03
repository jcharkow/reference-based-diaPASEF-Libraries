################
## Runall OSW ##
################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e

inputFolder="../../data/2021-06-26-K562-GPF/mzML"


m400=${inputFolder}/RostDIA400_SP2um_90min_250ngK562_100nL_Slot1-5_1_1316_6-27-2021.mzML
m460=${inputFolder}/RostDIA460_SP2um_90min_250ngK562_100nL_Slot1-5_1_1317_6-27-2021.mzML   
m520=${inputFolder}/RostDIA520_SP2um_90min_250ngK562_100nL_Slot1-5_1_1318_6-27-2021.mzML   
m580=${inputFolder}/RostDIA580_SP2um_90min_250ngK562_100nL_Slot1-5_1_1319_6-27-2021.mzML   
m640=${inputFolder}/RostDIA640_SP2um_90min_250ngK562_100nL_Slot1-5_1_1320_6-27-2021.mzML
m700=${inputFolder}/RostDIA700_SP2um_90min_250ngK562_100nL_Slot1-5_1_1321_6-27-2021.mzML
m760=${inputFolder}/RostDIA760_SP2um_90min_250ngK562_100nL_Slot1-5_1_1322_6-27-2021.mzML
m820=${inputFolder}/RostDIA820_SP2um_90min_250ngK562_100nL_Slot1-5_1_1323_6-27-2021.mzML
m880=${inputFolder}/RostDIA880_SP2um_90min_250ngK562_100nL_Slot1-5_1_1324_6-27-2021.mzML
m940=${inputFolder}/RostDIA940_SP2um_90min_250ngK562_100nL_Slot1-5_1_1325_6-27-2021.mzML
m1000=${inputFolder}/RostDIA1000_SP2um_90min_250ngK562_100nL_Slot1-5_1_1326_6-28-2021.mzML  
m1060=${inputFolder}/RostDIA1060_SP2um_90min_250ngK562_100nL_Slot1-5_1_1327_6-28-2021.mzML  
m1120=${inputFolder}/RostDIA1120_SP2um_90min_250ngK562_100nL_Slot1-5_1_1328_6-28-2021.mzML  

libPth=../../results/PeptDeep-NoMods-In-Silico-Library-Generation/
irtLin=${libPth}/2025-05-23-linear-irt.tsv
irtNonLin=${libPth}/2025-03-06-nonlinear-irt-in-silico.tsv
lib=${libPth}/2025-06-10-in-silico-lib-no-mods_fix_mods_filtered_6Frags_decoys_filtered.tsv.zst

sigOSW=../../bin/sif/2024-12-13-OSW-TSV-Lib.sif
sigProphet="../../bin/sif/2025-06-23-pyprophet.sif"
sigProphetXIC="../../bin/sif/2025-08-19-pyprophet-export-xics.sif"

checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $m400 $m460 $m520 $m580 $m640 $m700 $m760 $m820 $m880 $m940 $m1000 $m1060 $m1120
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 800"

	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtNonLin} ${fromMain}/${irtNonLin} ${output} True ${fromMain}/${sigOSW} $additionalParam

	# Convert OSW File to .oswpq
	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
		checkAndRunSbatch ${output}.parquet ${fromMain}/${scripts}/run_pyprophet_export_sqmass.sh -f ${output}.sqMass -p ${output}.osw -s ${fromMain}/${sigProphetXIC}
	fi
	cd ../..
done

### merge the pyprophet into oswpq file
fromMain="../../"
checkCreateFolder pyprophet_XGB
checkAndRunSbatch merged.oswpqd ${fromMain}/${scripts}/run_pyprophet_parquet_multiple.sh -o merged.oswpq -a '--classifier=XGBoost --ss_main_score=var_yseries_score' -s ${fromMain}/${sigProphet} \
	-f ../$(basename ${m400/.mzML})/oswOut/$(basename ${m400/.mzML}).oswpq \
	-f ../$(basename ${m460/.mzML})/oswOut/$(basename ${m460/.mzML}).oswpq \
	-f ../$(basename ${m520/.mzML})/oswOut/$(basename ${m520/.mzML}).oswpq \
	-f ../$(basename ${m580/.mzML})/oswOut/$(basename ${m580/.mzML}).oswpq \
	-f ../$(basename ${m640/.mzML})/oswOut/$(basename ${m640/.mzML}).oswpq \
	-f ../$(basename ${m700/.mzML})/oswOut/$(basename ${m700/.mzML}).oswpq \
	-f ../$(basename ${m760/.mzML})/oswOut/$(basename ${m760/.mzML}).oswpq \
	-f ../$(basename ${m820/.mzML})/oswOut/$(basename ${m820/.mzML}).oswpq \
	-f ../$(basename ${m880/.mzML})/oswOut/$(basename ${m880/.mzML}).oswpq \
	-f ../$(basename ${m940/.mzML})/oswOut/$(basename ${m940/.mzML}).oswpq \
	-f ../$(basename ${m1000/.mzML})/oswOut/$(basename ${m1000/.mzML}).oswpq \
	-f ../$(basename ${m1060/.mzML})/oswOut/$(basename ${m1060/.mzML}).oswpq \
	-f ../$(basename ${m1120/.mzML})/oswOut/$(basename ${m1120/.mzML}).oswpq


cd ..
checkCreateFolder pyprophet_LDA
checkAndRunSbatch merged.oswpqd ${fromMain}/${scripts}/run_pyprophet_parquet_multiple.sh -o merged.oswpq -a '--classifier=SVM' -s ${fromMain}/${sigProphet} \
	-f ../$(basename ${m400/.mzML})/oswOut/$(basename ${m400/.mzML}).oswpq \
	-f ../$(basename ${m460/.mzML})/oswOut/$(basename ${m460/.mzML}).oswpq \
	-f ../$(basename ${m520/.mzML})/oswOut/$(basename ${m520/.mzML}).oswpq \
	-f ../$(basename ${m580/.mzML})/oswOut/$(basename ${m580/.mzML}).oswpq \
	-f ../$(basename ${m640/.mzML})/oswOut/$(basename ${m640/.mzML}).oswpq \
	-f ../$(basename ${m700/.mzML})/oswOut/$(basename ${m700/.mzML}).oswpq \
	-f ../$(basename ${m760/.mzML})/oswOut/$(basename ${m760/.mzML}).oswpq \
	-f ../$(basename ${m820/.mzML})/oswOut/$(basename ${m820/.mzML}).oswpq \
	-f ../$(basename ${m880/.mzML})/oswOut/$(basename ${m880/.mzML}).oswpq \
	-f ../$(basename ${m940/.mzML})/oswOut/$(basename ${m940/.mzML}).oswpq \
	-f ../$(basename ${m1000/.mzML})/oswOut/$(basename ${m1000/.mzML}).oswpq \
	-f ../$(basename ${m1060/.mzML})/oswOut/$(basename ${m1060/.mzML}).oswpq \
	-f ../$(basename ${m1120/.mzML})/oswOut/$(basename ${m1120/.mzML}).oswpq

cd ..
## pyprophet create library
module load apptainer
sifProphetNew="../../bin/sif/2025-07-11-pyprophet_createLib.sif"
sifProphetNew2="../../bin/sif/2025-08-11-pyprophet-nativeRT-libExport.sif" # image deleted due to bugs, could use 2025-08-12-export_lib_unscored.sif
libPrefix=2025-07-11-osw-peptdeepNoMods-gpf-refined
if [[ -d pyprophet_XGB/merged.oswpqd ]]
then

	fromMain="../"
	checkAndRun ${libPrefix}.tsv apptainer exec ${fromMain}/${sifProphetNew} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}.tsv
	checkAndRun ${libPrefix}_onlyFilter.tsv apptainer exec ${fromMain}/${sifProphetNew} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}_onlyFilter.tsv --no-rt_calibration --no-intensity_calibration --no-im_calibration
	checkAndRun ${libPrefix}_nativeRT.tsv apptainer exec ${fromMain}/${sifProphetNew2} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}_nativeRT.tsv --rt_unit RT
fi
