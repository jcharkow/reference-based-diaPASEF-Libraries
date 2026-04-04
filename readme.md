This repository contains the scripts, notebooks and results associated with the manuscript "Reference-Based Library Construction Improves Performance in diaPASEF Workflows"

Notebooks for creating figures in the manuscript can be found in the `figures` folder. Note that results are not included. 

Some key scripts are found in the `src` folder and include:

1. `createGPFLibraryDIANNStringent.py` - Create library from DIA-NNs results.tsv file 
2. `createGPFLibrary.py` - Create library from OpenSWATH from legacy .parquet file format, new libraries should be created using the `pyprophet library` command
3. `run_osw.sh`, `run_pyprophet_export_parquet_scoring.sh`  `run_pyprophet_parquet.sh` - Main files for running OpenSWATH and PyProphet
4. `run_diann_fasta.sh` main script for running DIA-NN

