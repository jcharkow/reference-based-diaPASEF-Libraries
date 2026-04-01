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

libPath="../K562-Exp-Lib-Analysis/formattedLib/"
irtNonLin=${libPath}/2025-03-06-nonLin-iRT.tsv
lib=${libPath}/easypqp_lib_openswath_osw_6Frags_decoys.pqp
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif
#sigProphet="../../bin/sif/2024-12-12-pyprophet-57a6e5f.sif"
sigProphet="../../bin/sif/2025-08-12-export_lib_unscored.sif"

checkCreateFolder osw
### Run OSW Workflow ####
for mzml in $m400 $m460 $m520 $m580 $m640 $m700 $m760 $m820 $m880 $m940 $m1000 $m1060 $m1120
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../../"

	# Run OSW
	checkCreateFolder oswOut
	additionalParam="-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 600"
	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw.sh ${fromMain}/${mzml} ${fromMain}/${lib} ${fromMain}/${irtNonLin} ${fromMain}/${irtNonLin} ${output} True ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi
	cd ../..
done


#### Perform merged pyprophet analysis
#Run Pyprophet 
echo $(pwd)
echo output ${output}
if [[ -d ${output}/oswOut/${output}.oswpq ]]
then
	checkCreateFolder pyprophet_XGB
	fromMain="../../"
	checkAndRunSbatch merged.oswpqd ${fromMain}/${scripts}/run_pyprophet_parquet_multiple.sh -o merged.osw -a '--classifier=XGBoost --ss_main_score=var_dotprod_score' -s ${fromMain}/${sigProphet} \
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
sifProphetNew="../../bin/sif/2025-07-10-pyprophet_createLib.sif"
sifProphetNew2="../../bin/sif/2025-08-12-export_lib_unscored.sif"
libPrefix=2025-08-14-osw-expLib-gpf-refined
if [[ -d pyprophet_XGB/merged.oswpqd ]]
then

	fromMain="../"
	checkAndRun ${libPrefix}.tsv apptainer exec ${fromMain}/${sifProphetNew} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}.tsv
	checkAndRun ${libPrefix}_onlyFilter.tsv apptainer exec ${fromMain}/${sifProphetNew} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}_onlyFilter.tsv --no-rt_calibration --no-intensity_calibration --no-im_calibration
	checkAndRun ${libPrefix}_nativeRT.tsv apptainer exec ${fromMain}/${sifProphetNew2} pyprophet export library --in pyprophet_XGB/merged.oswpqd --out ${libPrefix}_nativeRT.tsv --rt_unit RT
fi

cd ..

######################### STEP 2 #########################################################
############# Now that have the native RT library can do another OSW analysis for TL ######
###########################################################################################
checkCreateFolder osw_xtra_frags
fromMain="../"

refinedLib=${fromMain}/osw/${libPrefix}_nativeRT.tsv

lib=${libPath}/easypqp_lib_openswath_osw_6Frags_decoys.pqp
origLib=${fromMain}/${libPath}/easypqp_lib_openswath.tsv
PYTHON_PATH=~/jos_jup/bin/python
sigOSW=../../bin/sif/openms-executables-sif_3.2.0.sif

# Generate output filename
output_file="$(basename "${origLib/.tsv/_Only_Identified_OSW.tsv}")"

# Execute Python code with bash variables
checkAndRun ${output_file} ${PYTHON_PATH} << EOF
import polars as pl

# Use the bash variables
refined_lib_path = "$refinedLib"
lib_silico_path = "$origLib"
output_path = "$output_file"

print("Loading refined library")
refined_lib = pl.read_csv(refined_lib_path, separator='\t')
refined_lib = refined_lib.with_columns(
    (pl.col('ModifiedPeptideSequence') + pl.col('PrecursorCharge').cast(pl.Utf8)).alias('Precursor')
)

print("Loading unrefined library (all frags)")
lib_silico = pl.read_csv(lib_silico_path, separator='\t')
lib_silico = lib_silico.with_columns(
    (pl.col('ModifiedPeptideSequence') + pl.col('PrecursorCharge').cast(pl.Utf8)).alias('Precursor')
)
lib_silico = lib_silico.drop(['NormalizedRetentionTime', 'PrecursorIonMobility'])

# Filter lib_silico to only include precursors found in refined_lib
precursors_to_keep = refined_lib.select(['Precursor', 'NormalizedRetentionTime', 'PrecursorIonMobility']).unique()
lib_silico_filtered = lib_silico.join(precursors_to_keep, on='Precursor', how='inner')

# Save the filtered results
lib_silico_filtered.write_csv(output_path, separator='\t')
print(f"Filtered library saved to: {output_path}")

# Print fragments per precursor statistics
fragments_per_precursor = lib_silico_filtered.group_by('Precursor').agg(pl.len().alias('fragment_count'))
print(f"\nFragments per precursor statistics:")
print(f"Total precursors: {len(fragments_per_precursor)}")
print(f"Average fragments per precursor: {fragments_per_precursor['fragment_count'].mean():.2f}")
print(f"Min fragments per precursor: {fragments_per_precursor['fragment_count'].min()}")
print(f"Max fragments per precursor: {fragments_per_precursor['fragment_count'].max()}")

# Show distribution
fragment_distribution = fragments_per_precursor.group_by('fragment_count').agg(
    pl.len().alias('precursor_count')
).sort('fragment_count')
print(f"\nFragment count distribution:")
for row in fragment_distribution.iter_rows(named=True):
    print(f"  {row['fragment_count']} fragments: {row['precursor_count']} precursors")
EOF


###########################################
# Run OpenSwathAssayGenerator
##########################################
baseLib=${output_file}
module load apptainer
checkAndRun ${baseLib/.tsv/_formatted.tsv} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} OpenSwathAssayGenerator -in ${baseLib} -out ${baseLib/.tsv/_formatted.tsv} -min_transitions 6 -max_transitions 12

##################################
# Convert to .pqp
#################################
checkAndRun ${baseLib/.tsv/_formatted.pqp} apptainer exec --bind $(pwd):/mnt --pwd /mnt ${fromMain}/${sigOSW} TargetedFileConverter -in ${baseLib/.tsv/_formatted.tsv} -out ${baseLib/.tsv/_formatted.pqp}

lib=${baseLib/.tsv/_formatted.pqp}
### Run OSW Workflow ####
doneOSW="true"
for mzml in $m400 $m460 $m520 $m580 $m640 $m700 $m760 $m820 $m880 $m940 $m1000 $m1060 $m1120
do
	output=$(basename ${mzml/.mzML})
	checkCreateFolder $output
	fromMain="../../"

	# Run OSW
	additionalParam="-ion_mobility_window 0.06 -rt_extraction_window 100"

	checkAndRunSbatch ${output}.osw ${fromMain}/${scripts}/run_osw_nativeRT.sh ${fromMain}/${mzml} ${fromMain}/osw_xtra_frags/${lib} ${output} False ${fromMain}/${sigOSW} $additionalParam

	if [[ -f ${output}.osw ]]
	then
		checkAndRunSbatch ${output}.oswpq ${fromMain}/${scripts}/run_pyprophet_export_parquet_scoring.sh -f ${output}.osw -s ${fromMain}/${sigProphet}
	fi

	if [[ ! -d ${output}.oswpq ]]
	then
		doneOSW="false"
	fi
	cd ..
done


#### Create the library 
set -x
if [[ ${doneOSW} == "true" ]]
then
	checkAndRun merged.oswpqd mkdir merged.oswpqd && cp -r $(basename ${m400/.mzML})/$(basename ${m400/.mzML}).oswpq \
			$(basename ${m460/.mzML})/$(basename ${m460/.mzML}).oswpq \
			$(basename ${m520/.mzML})/$(basename ${m520/.mzML}).oswpq \
			$(basename ${m580/.mzML})/$(basename ${m580/.mzML}).oswpq \
			$(basename ${m640/.mzML})/$(basename ${m640/.mzML}).oswpq \
			$(basename ${m700/.mzML})/$(basename ${m700/.mzML}).oswpq \
			$(basename ${m760/.mzML})/$(basename ${m760/.mzML}).oswpq \
			$(basename ${m820/.mzML})/$(basename ${m820/.mzML}).oswpq \
			$(basename ${m880/.mzML})/$(basename ${m880/.mzML}).oswpq \
			$(basename ${m940/.mzML})/$(basename ${m940/.mzML}).oswpq \
			$(basename ${m1000/.mzML})/$(basename ${m1000/.mzML}).oswpq \
			$(basename ${m1060/.mzML})/$(basename ${m1060/.mzML}).oswpq \
			$(basename ${m1120/.mzML})/$(basename ${m1120/.mzML}).oswpq merged.oswpqd/


	libOut=2025-08-15-exp-lib-refined_GPF_manyFrags_OSW.tsv 
	module load apptainer
	checkAndRun ${libOut} apptainer exec --pwd /mnt --bind $(pwd):/mnt ../${sifProphetNew2} pyprophet export library --in merged.oswpqd --out ${libOut}
fi
