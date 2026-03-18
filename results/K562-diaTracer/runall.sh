#!/bin/bash

scripts="../../src"

source ${scripts}/run_helper.sh
set -e

./runall_diann.sh
./runall_osw.sh
