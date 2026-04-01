#!/usr/bin/env python3
import os
import subprocess
import glob
import re
import sys
from collections import defaultdict

def check_create_folder(folder_name):
    """Create folder if it doesn't exist"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    os.chdir(folder_name)

def check_and_run_sbatch(report_file, script_path, *args):
    """Run sbatch command if report file doesn't exist"""
    if not os.path.exists(report_file):
        # Construct the sbatch command
        cmd = ["sbatch", script_path] + list(args)
        print(f"Submitting job: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            raise
    else:
        print(f"Report file {report_file} already exists, skipping.")

def check_and_run(report_file, script_path, *args):
    """Run command directly (without sbatch) if report file doesn't exist"""
    if not os.path.exists(report_file):
        # Construct the command to run directly
        cmd = [script_path] + list(args)
        print(f"Running command: {' '.join(cmd)}")
        try:
            # Run without capturing output - prints in real time
            result = subprocess.run(cmd, check=True, text=True)
            print("Command completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            raise
    else:
        print(f"Report file {report_file} already exists, skipping.")

# Function to extract dilution and replicate from directory name
def extract_info(dirname: str) -> tuple:
    dilution_match = re.search(r'(\d+)(?=pg_)', dirname)
    replicate_match = re.search(r'PyDIA_(\d+)_', dirname)
    
    dilution = dilution_match.group(1) if dilution_match else "unknown"
    replicate = replicate_match.group(1) if replicate_match else "unknown"
    
    return dilution + 'pg', replicate

def get_appropriate_libraries(sample_info):
    """
    Determine which libraries to use for a given sample file. Use the same library for every sample of the same dilution (not a different library per replicate)
    """
    # Extract the dilution using regex
    dilution_match = re.search(r'(\d+)(?=pg_)', sample_info)
    if not dilution_match:
        return []  # No dilution found
        
    dilution = int(dilution_match.group(1))
    
    # Libraries are always from replicate 1
    libs_out = []
    if dilution < 100:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-100pg-rep3")
    if dilution < 250:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-250pg-rep4")
    if dilution < 500:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-500pg-rep3")
    if dilution < 1000:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-1000pg-rep3")
    if dilution < 2500:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-2500pg-rep3")
    if dilution < 5000:
        libs_out.append("2025-07-23-Refine-diaTracer-DIANN-5000pg-rep1")
        
    return libs_out

# Define paths relative to main folder
main_dir = os.getcwd()
scripts_dir = "../../src"  # Corrected path to scripts directory
scripts_path = os.path.abspath(os.path.join(main_dir, scripts_dir))
run_diann_script = os.path.join(scripts_path, "run_diann_fasta.sh")

# Input folder path
input_folder = "../../data/2025-05-UltraLowDilutions/DDM02"
input_folder_abs = os.path.abspath(os.path.join(main_dir, input_folder))

samples = defaultdict(list)
for exp in os.listdir(input_folder_abs):
    dilution, replicate = extract_info(exp)
    samples[dilution].append(os.path.join(input_folder_abs, exp))

# Define tool paths with absolute paths
sif_diann = os.path.abspath(os.path.join(main_dir, "../../bin/sif/2024-12-27-diann-1_9_2.sif"))
fasta = os.path.abspath(os.path.join(main_dir, "../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"))

# Library paths - now we need both directories
lib_path_dilutions = "refinedMasterLibs"
lib_path_dilutions_abs = os.path.abspath(os.path.join(main_dir, lib_path_dilutions))


def get_library_path(lib_id):
    """Determine which library path to use based on the library identifier"""
    # Check if the library exists in the Dilutions-diaTracer folder
    pth_out = os.path.join(lib_path_dilutions_abs, lib_id + '.tsv')
    if os.path.exists(pth_out):
        return pth_out
    else:
        raise Exception(f"Library '{lib_id}' not found in expected locations!")
        
def process_samples(use_qvalue_one=False, use_sbatch=True):
    """
    Process all samples with their appropriate libraries
    
    Parameters:
    - use_qvalue_one: bool, whether to use qvalue=1.0 parameter
    - use_sbatch: bool, whether to use sbatch for job submission
    """
    
    # Store original directory
    original_dir = os.getcwd()
    
    # Create main folder
    folder_name = "diann_full" if use_qvalue_one else "diann"
    check_create_folder(folder_name)
    
    # Process each dilution group
    for dilution, dilution_samples in samples.items():
        # Skip 500ng samples as they are the highest concentration (no libraries to search against)
        if dilution == "5000pg":
            continue
            
        # Create folder for this dilution
        check_create_folder(dilution)
        
        # Process each sample in this dilution
        for sample in dilution_samples:
            sample_basename = os.path.basename(sample).replace(".d", "")
            check_create_folder(sample_basename)
            
            # Get appropriate libraries for this sample (always using replicate 1 libraries)
            lib_identifiers = get_appropriate_libraries(sample)
            
            for lib_id in lib_identifiers:
                # Create folder for this library
                check_create_folder(f"{lib_id}_lib")
                
                # Define parameters
                additional_param = "--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info"
                if use_qvalue_one:
                    additional_param += " --qvalue 1.0"
                
                # Get the appropriate library file path
                library_file = get_library_path(lib_id)
                
                # Run DIA-NN using sbatch or directly
                if use_sbatch:
                    check_and_run_sbatch("report.tsv", run_diann_script, sample, library_file, fasta, sif_diann, additional_param)
                else:
                    check_and_run("report.tsv", run_diann_script, sample, library_file, fasta, sif_diann, additional_param)
                
                # Go back to sample folder
                os.chdir("..")
            
            # Go back to dilution folder
            os.chdir("..")
        
        # Go back to main folder
        os.chdir("..")
    
    # Go back to original directory
    os.chdir(original_dir)

def main():
    # Process samples with default parameters
    use_sbatch = True
    
    # Get command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["nosbatch", "no-sbatch", "direct"]:
            use_sbatch = False
            print("Running without sbatch (direct execution)")
        elif sys.argv[1].lower() in ["sbatch", "cluster"]:
            use_sbatch = True
            print("Running with sbatch (cluster submission)")
    
    # Run with standard parameters
    process_samples(use_qvalue_one=False, use_sbatch=use_sbatch)
    
    # Run with qvalue=1.0
    process_samples(use_qvalue_one=True, use_sbatch=use_sbatch)

if __name__ == "__main__":
    main()
