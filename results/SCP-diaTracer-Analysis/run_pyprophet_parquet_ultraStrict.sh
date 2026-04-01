#!/bin/sh
#SBATCH --account=def-hroest
#SBATCH --mem-per-cpu=8000Mb       # memory per cpu - match with treads argument when running
#SBATCH --time=0-02:59            # time (DD-HH:MM), this is shortest queue length (partition lengths <3hr, <12hr, <24hr, <72hr, 7days, 28days)
#SBATCH --job-name=pyProphet_sig
#SBATCH --cpus-per-task=1         # OpenMP job
#SBATCH --output=%x-%j.out

# This script is for running pyprophet on the cluster
# Takes an oswpq file in and does the scoring


echo $(date)
module load apptainer


# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

##Initialize variables
fileIn="" # should be .oswpq folder
additionalParam=""
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
    s)  sig=$OPTARG
	;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

echo "fIn: $fileIn" #
echo "additionalParam: $additionalParam"
echo "sig: $sig"

set -e


# On a LSF filesystem like graham it is considerd best practice to write the output of
# I/O intensive jobs to a temporary directory and to copy it to the final location only
# at the end of the job.
TMPDIR=$SLURM_TMPDIR
if [ -z ${SLURM_TMPDIR+x} ]; then
  TMPDIR=~/links/scratch/
else
  TMPDIR=$SLURM_TMPDIR
fi
echo " Temporary directory used: $TMPDIR "

# only one file, get I/O error if do not copy over to current directory
cp -r ${fileIn} ${TMPDIR}
cp ${sig} ${TMPDIR}
osw=$(basename ${fileIn})

pushd .
cd $TMPDIR
scoreCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt $(basename ${sig}) pyprophet score --in=${osw} --level=ms1ms2 --threads=1 ${additionalParam}"
echo ${scoreCommand}
$scoreCommand


peptideCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt $(basename ${sig}) pyprophet infer peptide --in=${osw} --context=global --pi0_lambda 0.001 0 0" 
echo ${peptideCommand}
$peptideCommand


proteinCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt $(basename ${sig}) pyprophet infer protein --in=${osw} --context=global --pi0_lambda 0.001 0 0" 
echo ${proteinCommand}
$proteinCommand

libCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt $(basename ${sig}) pyprophet export library --in ${osw} --out ${osw/.oswpq}_lib.tsv"
echo ${libCommand} 
$libCommand

# library only filtering
libCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt $(basename ${sig}) pyprophet export library --in ${osw} --out ${osw/.oswpq}_lib_onlyFilter.tsv --no-rt_calibration --no-intensity_calibration --no-im_calibration"
echo ${libCommand} 
$libCommand

echo "done running"
popd
# To move the output to a desired directory the ownership has to be changed to the
# appropriate user first. Make sure you have write permissions in the output dir.
# @TODO find a more elegant way to move this. For now the fileformats have to be changed here
# everytime they are changed above!! 
set +e # turn off errors so can copy everything
popd .
cp -r $TMPDIR ~/scratch
user=$(whoami)

chown -R $user:def-hroest $TMPDIR/${osw} # !!changeit!!
mv $TMPDIR/${osw} ./ # !!changeit!!

chown $user:def-hroest $TMPDIR/*.pdf # !!changeit!!
mv $TMPDIR/*.pdf ./ # !!changeit!!

chown $user:def-hroest $TMPDIR/*.csv # !!changeit!!
mv $TMPDIR/*.csv ./ # !!changeit!!

chown $user:def-hroest $TMPDIR/*.log # !!changeit!!
mv $TMPDIR/*.log ./ # !!changeit!!

chown $user:def-hroest $TMPDIR/*.tsv # !!changeit!!
mv $TMPDIR/*.tsv ./ # !!changeit!!
