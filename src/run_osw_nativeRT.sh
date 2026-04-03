#!/bin/sh
#SBATCH --account=def-hroest
#SBATCH --mem-per-cpu=8000M       # memory per cpu - match with treads argument when running
#SBATCH --time=0-02:59            # time (DD-HH:MM), this is shortest queue length (partition lengths <3hr, <12hr, <24hr, <72hr, 7days, 28days)
#SBATCH --cpus-per-task=8         # OpenMP job
#SBATCH --job-name=openSWATH
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
output=$3
doChrom=$4
sig=$5
shift 5
additionalparam=$@

echo $(pwd)

# Usage
if [ "$inputfile" == "" ]; then
    echo "Not all input arguments were specified, aborting..."
    echo ""
    echo "OpenSwathWorkflow on compute canada cluster -- Complete workflow to run OpenSWATH"
	echo "-----------------------------------------------------------------";
	echo "Executes the OpenSwathWorkfolw on the graham cluster. To use a specific build of openMS please specify the variable buildpath in the script. The commandline arguments are listed below. OpenSwathworkflow can take additional arguments that have to be specified in the script directly if desired. For more information run: $buildpath/bin/OpenSwathWorkfow";
	echo "";
	echo "USAGE INFORMATION:";
	echo "";
	echo "sbatch run_osw.sh inputfile library irt_lib output doChrom treads user";
	echo "";
	echo "inputfile		Input files separated by blank (valid formats: 'mzML', 'mzXML', 'sqMass')";
	echo "library	        Transition file ('TraML','tsv','pqp') (valid formats: 'traML', 'tsv', 'pqp')";
	echo "irt_lib	        OSW output file (PyProphet compatible SQLite file) (valid formats: 'osw')";
	echo "nonlin_irt_lib	OSW output file (PyProphet compatible SQLite file) (valid formats: 'osw')";
	echo "output	        OSW output file (PyProphet compatible SQLite file) (valid formats: 'osw')";
	echo "doChrom           Whether to output chromatographic traces (valid inputs: True, False)";

	echo "advanced		Additional parameters in the format \"-parameter value\". Can be multiple osw parameters not specified in the script";
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
touch $output
ckFileW $output "Output files"
rm $output
echo "The output will be stored in $output"
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


OUTCHROM=""
if [[ "$doChrom" == "True" ]]
then
    # Change to the desired output format (e.g. mzML)
    OUTCHROM="-out_chrom output.sqMass" # !!changeit!!
    echo "Chromatogram output is enabled."
fi



dir=`pwd`
echo "Current directory: $dir "

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


## Copy input files to temporary directory 
cp ${inputfile} $TMPDIR
cp ${library} $TMPDIR

# For more info on which parameters can be set run OpenSwathWorkflow --helphelp
RTNORM="-Library:retentionTimeInterpretation seconds"

# Set the advanced parameters for the workflow
#ADVANCED="-use_ms1_traces -mz_correction_function quadratic_regression_delta_ppm -min_coverage 0.1" # !!changeit!!
ADVANCED="-enable_ms1 true -mz_correction_function quadratic_regression_delta_ppm -min_coverage 0.1" # !!changeit!!

# Has to be set only if the windows cannot be read from the input file
SWATH_WIN="" # !!changeit!!

#ION_MOBILITY_EXTRACTION="-irt_im_extraction_window -1 -ion_mobility_window 0.08" # !!changeit!!
# The extraction window in m/z dimension. Will depend on the instrument's mass accuracy
MZRTEXTRACTION_WINDOW="-mz_extraction_window 25 -mz_extraction_window_unit ppm -mz_extraction_window_ms1 25 -mz_extraction_window_ms1_unit ppm -irt_mz_extraction_window_unit ppm  -irt_mz_extraction_window 40" # !!changeit!!

########### Not sure if need -extra_rt_extraction_window 100 ########

# Ion mobility calibration
CALIBRATION="-Calibration:debug_mz_file $TMPDIR/${output}_debug_ppmdiff.txt -Calibration:debug_im_file $TMPDIR/${output}_debug_imdiff.txt"

SCORING="-Scoring:TransitionGroupPicker:min_peak_width 5.0 -Scoring:TransitionGroupPicker:PeakPickerChromatogram:sgolay_frame_length 11 -Scoring:stop_report_after_feature 5 -Scoring:Scores:use_ion_mobility_scores -Scoring:TransitionGroupPicker:compute_peak_shape_metrics"
 
ADDITIONAL_PARAM=$additionalparam

DEBUG="-debug 0"

############################################
# Run OpenSwath
############################################
runcommand="apptainer exec --bind $TMPDIR:/mnt --pwd /mnt ${sig} OpenSwathWorkflow \
    -in "$(basename ${inputfile})" \
    -tr "$(basename ${library})" \
    -out_osw ${output}.osw $OUTCHROM \
    $ADVANCED \
    $SWATH_WIN \
    $CALIBRATION \
    $MZRTEXTRACTION_WINDOW \
    $RTNORM \
    $SCORING \
    -batchSize 250\
    -readOptions cacheWorkingInMemory \
    -tempDirectory ./ \
    -threads $threads \
    $ADDITIONAL \
    $ADDITIONAL_PARAM \
    $DEBUG \
    -force \
    -pasef"
echo "The run command was:"
echo $runcommand

# Excecute OpenSwathWorkflow
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
cp -r $TMPDIR ~/scratch
user=$(whoami)

mv $TMPDIR/${output}.osw ${output}.osw # !!changeit!!
chown $user:rrg-hroest $TMPDIR/${output}.osw # !!changeit!!
mv $TMPDIR/${output}.osw ${output}.osw # !!changeit!!

if [[ "$doChrom" == "True" ]]
then
    chown $user:rrg-hroest $TMPDIR/output.sqMass # !!changeit!!
    mv $TMPDIR/output.sqMass ${output}.sqMass # !!changeit!!
fi

chown $user:rrg-hroest $TMPDIR/${output}_debug_irt.mzML # !!changeit!!
mv $TMPDIR/${output}_debug_irt.mzML ${output}_debug_irt.mzML # !!changeit!!

chown $user:rrg-hroest $TMPDIR/${output}_debug_ppmdiff.txt
mv $TMDIR/${output}_ms1_debug_ppmdiff.txt ${output}_ms1_debug_ppmdiff.txt
