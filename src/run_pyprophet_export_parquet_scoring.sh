#!/bin/sh
#SBATCH --account=def-hroest
#SBATCH --mem-per-cpu=8000Mb       # memory per cpu - match with treads argument when running
#SBATCH --time=0-02:59            # time (DD-HH:MM), this is shortest queue length (partition lengths <3hr, <12hr, <24hr, <72hr, 7days, 28days)
#SBATCH --job-name=pyProphet_sig
#SBATCH --cpus-per-task=8         # OpenMP job
#SBATCH --output=%x-%j.out

# This script is for converting the .osw file to a .oswpq file (parquet format split) for pyprophet

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
    s)  sig=$OPTARG
	;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

echo "fIn: $fileIn"
echo "sig: $sig"

set -e

# On a LSF filesystem like graham it is considerd best practice to write the output of
# I/O intensive jobs to a temporary directory and to copy it to the final location only
# at the end of the job.
TMPDIR=$SLURM_TMPDIR
if [ -z ${SLURM_TMPDIR+x} ]; then
  TMPDIR=~/scratch
else
  TMPDIR=$SLURM_TMPDIR
fi
echo " Temporary directory used: $TMPDIR "

# only one file, get I/O error if do not copy over to current directory
cp ${fileIn} ${TMPDIR}
osw=$(basename ${fileIn})

exportCommand="apptainer exec --cleanenv --bind ${TMPDIR}:/mnt --pwd /mnt ${sig} pyprophet export parquet --in=${osw} --out=${osw}pq --split_transition_data"
echo $exportCommand
$exportCommand

echo "done running"
# To move the output to a desired directory the ownership has to be changed to the
# appropriate user first. Make sure you have write permissions in the output dir.
# @TODO find a more elegant way to move this. For now the fileformats have to be changed here
# everytime they are changed above!! 
set +e # turn off errors so can copy everything
cp -r $TMPDIR ~/scratch
user=$(whoami)

chown -R $user:def-hroest $TMPDIR/${osw}pq # !!changeit!!
mv $TMPDIR/${osw}pq ./ # !!changeit!!
