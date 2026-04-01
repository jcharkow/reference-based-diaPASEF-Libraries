#########################
### Run DIA-NN Workflow #
#########################
scripts="../../src"

source ${scripts}/run_helper.sh
set -e


inputFolder="../../data/2021-03-09-Runs/d"

d_1ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-1ng_DIA_Slot1-4_1_552_3-8-2021.d
d_5ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-5ng_DIA_Slot1-4_1_551_3-8-2021.d
d_25ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-25ng_DIA_Slot1-5_1_550_3-7-2021.d
d_100ng=${inputFolder}/90min-SP-30cm-2um-K562-100nL-100ng_DIA_Slot1-5_1_549_3-7-2021.d

sifDiann="../../bin/sif/2024-12-27-diann-1_9_2.sif"
fasta="../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"

checkCreateFolder diann

######################
### Analyze Library ##
######################
libPth=../Dilutions-K562-PanHuman-Library/my_diann_libGen/
for d in $d_1ng $d_5ng $d_25ng $d_100ng
do
	### get the dilution number 
	dilution_mzml=${d%ng_DIA_Slot1*}
	dilution_mzml=${dilution_mzml#*100nL-}
	checkCreateFolder ${dilution_mzml}ng
	fromMain="../../"
	for lib in $(ls ${fromMain}/${libPth})
	do
		if [[ ${lib} == *-Lib.tsv ]]
		then
			dilution_lib=${lib%ng-Lib.tsv}
			dilution_lib=${dilution_lib#*DIANN-}
			echo ${dilution_lib}
			if [[ $(( dilution_mzml < dilution_lib )) == 1 ]]
			then
				fromMain="../../../"
				additionalParam="--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"
				checkCreateFolder ${dilution_lib}ng_lib
				output=$(basename -s .d ${d}) # the output file path 
				checkAndRunSbatch report.tsv ${fromMain}/${scripts}/run_diann_fasta.sh ${fromMain}/${d} ${fromMain}/${libPth}/${lib} ${fromMain}/${fasta} ${fromMain}/${sifDiann} ${additionalParam}
				cd ..
			fi
		fi
	done
	cd ..
done
cd ..
