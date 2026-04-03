#!/bin/sh
#SBATCH --account=def-hroest
#SBATCH --mem-per-cpu=32Gb       # memory per cpu - match with treads argument when running
#SBATCH --time=0-11:59            # time (DD-HH:MM), this is shortest queue length (partition lengths <3hr, <12hr, <24hr, <72hr, 7days, 28days)
#SBATCH --job-name=pyProphet_sig
#SBATCH --cpus-per-task=1         # OpenMP job
#SBATCH --output=%x-%j.out

# This script is for running pyprophet on the cluster
# This is the updated version, the old version is still saved for usage with older experiments however this script is more versatile

# This script uses the new identification report ver2 script


echo $(date)
module load apptainer


# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

##Initialize variables
fileIn=""
additionalParam=""
lib=""
output="merged.osw"
while getopts ":h:?:f:a:l:o:s:" opt; do
    case "$opt" in
    h|\?)
        showhelp
        exit 0
        ;;
    f)  fileIn=$OPTARG
        ;;
    a)  additionalParam=$OPTARG
        ;;
    o)  output=$OPTARG
	;;
    l)  lib=$OPTARG
	;;
    s)  sig=$OPTARG
	;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

echo "fIn: $fileIn"
echo "additionalParam: $additionalParam"
echo "Lib: $lib"
echo "output: $output"
echo "sig: $sig"

set -e


# only one file, get I/O error if do not copy over to current directory
cp ${fileIn} ./
osw=$(basename ${fileIn})


scoreCommand="apptainer exec --cleanenv --no-home --bind ./:/mnt --pwd /mnt ${sig} pyprophet score --in=${osw} --level=ms1ms2 --threads=1 ${additionalParam}"
echo ${scoreCommand}
$scoreCommand


peptideCommand="apptainer exec --cleanenv --no-home --bind ./:/mnt --pwd /mnt ${sig} pyprophet peptide --in=${osw} --context=global" 
echo ${peptideCommand}
$peptideCommand


proteinCommand="apptainer exec --cleanenv --no-home --bind ./:/mnt --pwd /mnt ${sig} pyprophet protein --in=${osw} --context=global" 
echo ${proteinCommand}
$proteinCommand


exportCommand="apptainer exec --bind ./:/mnt --pwd /mnt ${sig} pyprophet export-parquet --in=${osw}"
echo $exportCommand
$exportCommand
