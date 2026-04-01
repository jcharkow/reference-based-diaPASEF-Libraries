# Here format the library for usage with OpenSWATH
set -e
scripts="scripts"

#### Create OpenSWATH models
source ../../src/run_helper.sh
scripts="../../src"

checkCreateFolder osw_tl
cd ..

python ${scripts}/apply-TL.py --rsltsIn osw_xtra_frags/2025-08-14-bruker-lib-refined_GPF_manyFrags_OSW.tsv --libIn ../../data/BrukerLibrary/_ip2_ip2_data_paser_spectral_library__Bruker_Human.tsv --libOut osw_tl/2025-08-14-Bruker-TL-On-GPF-OSW.hdf --modelSuffix Bruker-GPF --model osw_models/ 
libName=osw_tl/2025-08-14-Bruker-TL-On-GPF-OSW.hdf

PYTHON_PATH="/home/roestlab/anaconda3/envs/peptdeep/bin/python"
PYTHON_PATH2="/home/roestlab/anaconda3/envs/jos_jup_3/bin/python"

source ../../src/run_helper.sh

checkAndRun ${libName/.hdf/.tsv} ${PYTHON_PATH} scripts/createTSVLib.py ${libName}
checkAndRun ${libName/.hdf/_fix_mods.tsv} ${PYTHON_PATH} scripts/fixModsOSW.py ${libName/.hdf/.tsv} 

