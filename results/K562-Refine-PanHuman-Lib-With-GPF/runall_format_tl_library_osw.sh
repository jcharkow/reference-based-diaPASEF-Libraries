# Here format the library for usage with OpenSWATH
# First .hdf library is produced on boltzmann cluster 

set -e
scripts="scripts"

libOut=2025-09-19-PHL-lib-TL-On-GPF-OSW.hdf
checkAndRun osw_tl/${libOut} python ${scripts}/apply-TL.py --rsltsIn osw_xtraFrags/2025-09-19-PHL-lib-refined_GPF_manyFrags_OSW.tsv --libIn ../PanHuman-Library-Creation/phl004_s32_imAppended_fixed_diann.tsv --libOut osw_tl/${libOut} --modelSuffix PanHuamn-GPF --model osw_models/ 

libName=osw_tl/2025-09-19-PHL-lib-TL-On-GPF-OSW.hdf

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"

source ../../src/run_helper.sh

checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLib.py ${libName}
checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixMods.py ${libName/.hdf/.tsv} 

