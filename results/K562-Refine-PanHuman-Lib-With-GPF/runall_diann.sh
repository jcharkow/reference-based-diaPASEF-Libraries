#!/bin/bash

# In this script use DIA-NN fully to generate the library (no involvement from OpenSwath)
#
##########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e



inputFolder="../../data/2021-06-26-K562-GPF/d"


d400=${inputFolder}/RostDIA400_SP2um_90min_250ngK562_100nL_Slot1-5_1_1316_6-27-2021.d
d460=${inputFolder}/RostDIA460_SP2um_90min_250ngK562_100nL_Slot1-5_1_1317_6-27-2021.d   
d520=${inputFolder}/RostDIA520_SP2um_90min_250ngK562_100nL_Slot1-5_1_1318_6-27-2021.d   
d580=${inputFolder}/RostDIA580_SP2um_90min_250ngK562_100nL_Slot1-5_1_1319_6-27-2021.d   
d640=${inputFolder}/RostDIA640_SP2um_90min_250ngK562_100nL_Slot1-5_1_1320_6-27-2021.d
d700=${inputFolder}/RostDIA700_SP2um_90min_250ngK562_100nL_Slot1-5_1_1321_6-27-2021.d
d760=${inputFolder}/RostDIA760_SP2um_90min_250ngK562_100nL_Slot1-5_1_1322_6-27-2021.d
d820=${inputFolder}/RostDIA820_SP2um_90min_250ngK562_100nL_Slot1-5_1_1323_6-27-2021.d
d880=${inputFolder}/RostDIA880_SP2um_90min_250ngK562_100nL_Slot1-5_1_1324_6-27-2021.d
d940=${inputFolder}/RostDIA940_SP2um_90min_250ngK562_100nL_Slot1-5_1_1325_6-27-2021.d
d1000=${inputFolder}/RostDIA1000_SP2um_90min_250ngK562_100nL_Slot1-5_1_1326_6-28-2021.d  
d1060=${inputFolder}/RostDIA1060_SP2um_90min_250ngK562_100nL_Slot1-5_1_1327_6-28-2021.d  
d1120=${inputFolder}/RostDIA1120_SP2um_90min_250ngK562_100nL_Slot1-5_1_1328_6-28-2021.d

# use the PanHuman library with the IM predicted by the in-silico alphapeptdeep 
lib="../PanHuman-Library-Creation/phl004_s32_imAppended_fixed_diann.tsv"
outLib="2025-05-29-GPF-Refined-Exp-Lib.parquet"

sifDiann="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas" #Note: This is not the fasta file from the library but use it anyways for library creation


fromMain="../"

checkCreateFolder diann-internals
additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info --reannotate --full-profiling --smart-profiling"

checkAndRunSbatch report.tsv ${fromMain}/${scripts}/create_gpf_lib_diann.sh ${fromMain}/${lib} ${fromMain}/${sifDiann} ${fromMain}/${fasta} ${outLib} 13 ${fromMain}/${d400} ${fromMain}/${d460} ${fromMain}/${d520} ${fromMain}/${d580} ${fromMain}/${d640} ${fromMain}/${d700} ${fromMain}/${d760} ${fromMain}/${d820} ${fromMain}/${d880} ${fromMain}/${d940} ${fromMain}/${d1000} ${fromMain}/${d1060} ${fromMain}/${d1120} ${additionalParam}
