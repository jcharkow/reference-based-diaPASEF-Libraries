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

libPath="../../results/K562-PanHuman-Analysis/formattedLib/"
irtNonLin=${libPath}/2025-03-06-nonLin-iRT.tsv
lib="../2025-11-27-PanHuman-Library-Full-New-Workflow-Prot-Annot-New-Decoys/formattedLib_osw/2025-11-27-phl004_s32_imAppended_reannotated_6Frags_decoys.pqp"
sigOSW="../../bin/sif/2025-06-19-with-irt-rtExt-param.sif"
sigOSWFull="../../bin/sif/openms-executables-sif_3.2.0.sif"
sifProphet="../../bin/sif/2025-07-11-pyprophet_createLib.sif"
sifProphet2="../../bin/sif/2025-09-18-pyprophet.sif"
sifProphetNew2="../../bin/sif/2025-08-12-export_lib_unscored.sif"

checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $m400 $m460 $m520 $m580 $m640 $m700 $m760 $m820 $m880 $m940 $m1000 $m1060 $m1120
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 1130 -irt_nonlinear_rt_extraction_window 3000"

	checkAndRunSbatch ${output}.osw ${fromMain}/../2025-06-23-PanHuman-Library-Full-New-Workflow/run_osw_tsv.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtNonLin} ${fromMain}/${irtNonLin} ${output} False ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sifProphet}
	fi
	cd ../..
done


#### Perform merged pyprophet analysis
#Run Pyprophet 
echo $(pwd)
if [[ -d ${output}/oswOut/${output}.oswpq ]]
then
	checkCreateFolder pyprophet_XGB
	fromMain="../../"

	checkAndRunSbatch merged.oswpqd ${fromMain}/${scripts}/run_pyprophet_parquet_multiple.sh -o merged.osw -a '--classifier=XGBoost --ss_main_score=var_dotprod_score' -s ${fromMain}/${sifProphet} \
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
	checkCreateFolder pyprophet_SVM
	checkAndRunSbatch merged.oswpqd ${fromMain}/${scripts}/run_pyprophet_parquet_multiple.sh -o merged.osw -a '--classifier=SVM --ss_scale_features' -s ${fromMain}/${sifProphet2} \
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


fi

##### Using the new scripts create the libraries for OpenSWATH
module load apptainer
libPrefix=2025-11-26-osw-PHL-gpf-refined-xgboost
if [[ -d pyprophet_XGB/merged.oswpqd ]]
then

	fromMain="../"
	checkAndRun ${libPrefix}.tsv apptainer exec ${fromMain}/${sifProphet} pyprophet --log-level debug export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}.tsv
	checkAndRun ${libPrefix}_onlyFilter.tsv apptainer exec ${fromMain}/${sifProphet} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}_onlyFilter.tsv --no-rt_calibration --no-intensity_calibration --no-im_calibration
fi

libPrefix=2025-11-26-osw-PHL-gpf-refined-SVM
if [[ -d pyprophet_SVM/merged.oswpqd ]]
then

	fromMain="../"
	checkAndRun ${libPrefix}.tsv apptainer exec ${fromMain}/${sifProphet2} pyprophet --log-level debug export library --in pyprophet_SVM/merged.oswpqd --out ${libPrefix}.tsv
	checkAndRun ${libPrefix}_onlyFilter.tsv apptainer exec ${fromMain}/${sifProphet2} pyprophet export library --in pyprophet_SVM/merged.oswpqd --out ${libPrefix}_onlyFilter.tsv --no-rt_calibration --no-intensity_calibration --no-im_calibration
	checkAndRun ${libPrefix}_nativeRT.tsv apptainer exec ${fromMain}/${sifProphet2} pyprophet export library --in pyprophet_SVM/merged.oswpqd --out ${libPrefix}_nativeRT.tsv --rt_unit RT
fi
cd ..
