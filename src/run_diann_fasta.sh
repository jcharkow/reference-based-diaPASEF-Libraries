#!/bin/sh
#SBATCH --account=def-hroest
#SBATCH --mem-per-cpu=8000M       # memory per cpu - match with treads argument when running
#SBATCH --time=0-02:59           # time (DD-HH:MM), this is shortest queue length (partition lengths <3hr, <12hr, <24hr, <72hr, 7days, 28days)
#SBATCH --cpus-per-task=4         # OpenMP job
#SBATCH --job-name=diaNN
#SBATCH --output=%x-%j.out

# this script has been modfiied to output chromatograms and also run my custom version of OpenSwath

##############################################
# Path to openMS build
##############################################
module load apptainer/1.2.4
set -e


##############################################
# Commandline arguments
##############################################

inputfile=$1
library=$2
fasta=$3
sig=$4
shift 4
additionalparam=$@

echo $(pwd)

# Usage
if [ "$inputfile" == "" ]; then
    echo "Not all input arguments were specified, aborting..."
    echo ""
    echo "dia-nn on graham-- Complete workflow to run dia-nn"
	echo "-----------------------------------------------------------------";
	echo "Executes the OpenSwathWorkfolw on the graham cluster. To use a specific build of openMS please specify the variable buildpath in the script. The commandline arguments are listed below. OpenSwathworkflow can take additional arguments that have to be specified in the script directly if desired. For more information run: $buildpath/bin/OpenSwathWorkfow";
	echo "";
	echo "USAGE INFORMATION:";
	echo "";
	echo "sbatch run_osw.sh inputfile library irt_lib output doChrom treads user";
	echo "";
	echo "inputfile		Input files separated by blank (valid formats: 'mzML', 'mzXML', 'sqMass')";
	echo "library	        Transition file ('tsv')";
	echo "fasta	        FASTA file ('.fasta')";
	echo "sig	        Singularity Container ('.sif')";
	echo "advanced		Additional parameters in the format \"-parameter value\"."
	echo "";
	exit 1;
fi

#############################################
# Helper functions
############################################

err() {
  echo "$1...exiting";
  exit 1; # any non-0 exit code signals an error
}

ckFile() {
  if [ ! -e "$1" ]; then
    err "$2 File '$1' not found";
  fi
}

ckFileSz() {
  ckFile $1 $2;
  SZ=`ls -l $1 | awk '{print $5}'`;
  if [ "$SZ" == "0" ]; then
    err "$2 file '$1' is zero length";
  else
    echo "$2 file '$1' checked";
  fi
}

ckFileW() {
    if [ ! -w "$1" ]; then
        err "$2 File '$1' not writeable";
    fi
}

###########################################
# Check input parameters
###########################################

# Exit if a file the user provided doesn't exist
echo ""
ckFileSz $inputfile "Input file"
ckFileSz $library "Transition file"
ckFileSz $fasta "fasta file"
ckFileSz $sig "sif file"
echo "Additional Param: $additionalparam"
echo ""

###########################################
# Parameter setup
###########################################

# Setup the number of threads used (through OpenMP).
# This needs to be set here only if the command is not run by slurm
threads=8 # !!changeit!!

if [ -z ${SLURM_CPUS_PER_TASK+x} ]; then
  export OMP_NUM_TREADS=$threads;
else
  export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK;
  threads=$SLURM_CPUS_PER_TASK
fi


dir=`pwd`
echo "Current directory: $dir "

# On a LSF filesystem like graham it is considerd best practice to write the output of
# I/O intensive jobs to a temporary directory and to copy it to the final location only
# at the end of the job.
TMPDIR=$SLURM_TMPDIR
if [ -z ${SLURM_TMPDIR+x} ]; then
  TMPDIR=/home/jsc718/scratch
else
  TMPDIR=$SLURM_TMPDIR
fi
echo " Temporary directory used: $TMPDIR "

## Copy input files to temporary directory 
cp -r ${inputfile} $TMPDIR
cp ${library} $TMPDIR
cp ${fasta} $TMPDIR

############################################
# Run dia-nn
############################################
runcommand="apptainer exec --bind $TMPDIR:/mnt --pwd /mnt ${sig} diann-linux \ 
	--f $(basename ${inputfile}) \
	--fasta $(basename ${fasta}) \
	--lib $(basename ${library}) \
	--threads ${threads} \
	--temp /mnt \
	${additionalparam}"

echo "The run command was:"
echo $runcommand
$runcommand

########################################
# Move output files
########################################
echo "done running"
# To move the output to a desired directory the ownership has to be changed to the
# appropriate user first. Make sure you have write permissions in the output dir.
# @TODO find a more elegant way to move this. For now the fileformats have to be changed here
# everytime they are changed above!! 
set +e # turn off errors so can copy everything
user=$(whoami)
cp -r $TMPDIR ~/scratch
chown $user:rrg-hroest $TMPDIR/* # !!changeit!!
cp $TMPDIR/report.tsv ./
