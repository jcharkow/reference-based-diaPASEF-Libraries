###### This is helper functions for any run script ######
######################## FUNCTIONS ###############################
checkCreateFolder() {

	folder=$1

	if ! [[ -d ${folder} ]]
	then
		mkdir ${folder}
	fi
	cd ${folder}
	echo Current Path: $(pwd)

}

checkAndRun() {
	outFile=$1
	shift 1
	cmd=("$@")

	echo Checking for file ${outFile} ...

	if ! [[ -f ${outFile} || -d ${outFile} ]]
	then
		echo "${cmd[@]}"
		"${cmd[@]}"
	fi
}


checkAndRunMock() {
	outFile=$1
	shift 1
	cmd=$@

	echo Checking for file ${outFile} ...

	if ! [[ -f ${outFile} || -d ${outFile} ]]
	then
		echo $cmd
	fi
}



checkAndRunSbatch() {
	outFile=$1
	shift 1
	cmd=("$@")

	if ! [[ -f ${outFile} || -d ${outFile} ]] 
	then
		echo "${cmd[@]}"
		sbatch "${cmd[@]}"
	fi
}

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
