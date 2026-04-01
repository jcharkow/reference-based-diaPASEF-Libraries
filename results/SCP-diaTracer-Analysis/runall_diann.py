#!/usr/bin/env python3
import os
import subprocess
import glob
import re
import sys
from collections import defaultdict

def check_create_folder(folder_name):
    """Create folder if it doesn't exist and change directory into it"""
    current_dir = os.getcwd()
    print(f"[DEBUG] check_create_folder: Current directory: {current_dir}")
    print(f"[DEBUG] check_create_folder: Checking/creating folder: {folder_name}")
    
    if not os.path.exists(folder_name):
        print(f"[DEBUG] check_create_folder: Creating folder: {folder_name}")
        os.makedirs(folder_name)
    else:
        print(f"[DEBUG] check_create_folder: Folder already exists: {folder_name}")
    
    os.chdir(folder_name)
    new_dir = os.getcwd()
    print(f"[DEBUG] check_create_folder: Changed directory to: {new_dir}")

def check_and_run_sbatch(report_file, script_path, *args):
    """Run sbatch command if report file doesn't exist"""
    current_dir = os.getcwd()
    print(f"[DEBUG] check_and_run_sbatch: Current directory: {current_dir}")
    print(f"[DEBUG] check_and_run_sbatch: Checking for report file: {report_file}")
    print(f"[DEBUG] check_and_run_sbatch: Script path: {script_path}")
    print(f"[DEBUG] check_and_run_sbatch: Arguments: {args}")
    
    if not os.path.exists(report_file):
        # Construct the sbatch command
        cmd = ["sbatch", script_path] + list(args)
        print(f"[DEBUG] check_and_run_sbatch: Report file {report_file} does not exist")
        print(f"[DEBUG] check_and_run_sbatch: Submitting job: {' '.join(cmd)}")
        print(f"[DEBUG] check_and_run_sbatch: Working directory: {current_dir}")
        
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"[DEBUG] check_and_run_sbatch: Job submitted successfully")
            print(f"[DEBUG] check_and_run_sbatch: Stdout: {result.stdout}")
            if result.stderr:
                print(f"[DEBUG] check_and_run_sbatch: Stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] check_and_run_sbatch: Command failed with return code {e.returncode}")
            print(f"[ERROR] check_and_run_sbatch: Command: {' '.join(e.cmd)}")
            print(f"[ERROR] check_and_run_sbatch: Stdout: {e.stdout}")
            print(f"[ERROR] check_and_run_sbatch: Stderr: {e.stderr}")
            raise
    else:
        print(f"[DEBUG] check_and_run_sbatch: Report file {report_file} already exists, skipping.")

def check_and_run(report_file, command, *args):
    """Run command directly (without sbatch) if report file doesn't exist"""
    current_dir = os.getcwd()
    print(f"[DEBUG] check_and_run: Current directory: {current_dir}")
    print(f"[DEBUG] check_and_run: Checking for report file: {report_file}")
    print(f"[DEBUG] check_and_run: Command: {command}")
    print(f"[DEBUG] check_and_run: Arguments: {args}")
    
    if not os.path.exists(report_file):
        # Construct the command to run directly
        cmd = [command] + list(args)
        print(f"[DEBUG] check_and_run: Report file {report_file} does not exist")
        print(f"[DEBUG] check_and_run: Running command: {' '.join(cmd)}")
        print(f"[DEBUG] check_and_run: Working directory: {current_dir}")
        
        try:
            # Run without capturing output - prints in real time
            result = subprocess.run(cmd, check=True, text=True)
            print(f"[DEBUG] check_and_run: Command completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] check_and_run: Command failed with return code {e.returncode}")
            print(f"[ERROR] check_and_run: Command: {' '.join(e.cmd)}")
            raise
    else:
        print(f"[DEBUG] check_and_run: Report file {report_file} already exists, skipping.")

def extract_dilution_and_replicate(dirname):
    """Extract dilution and replicate from directory name"""
    # Extract dilution: HeLa02DDM_{dilution}pg_
    dilution_match = re.search(r'HeLa02DDM_(\d+)pg_', dirname)
    # Extract replicate: _PyDIA_(\d+)_
    replicate_match = re.search(r'_PyDIA_(\d+)_', dirname)
    
    dilution = int(dilution_match.group(1)) if dilution_match else None
    replicate = int(replicate_match.group(1)) if replicate_match else None
    
    return dilution, replicate

def get_reference_replicate_for_dilution(dilution):
    """
    Get the reference replicate number for a given dilution based on the mapping:
    100pg -> replicate 3
    250pg -> replicate 4  
    500pg -> replicate 3
    1000pg -> replicate 3
    2500pg -> replicate 3
    5000pg -> replicate 1
    """
    dilution_to_replicate = {
        100: 3,
        250: 4,
        500: 3,
        1000: 3,
        2500: 3,
        5000: 1
    }
    
    reference_replicate = dilution_to_replicate.get(dilution)
    if reference_replicate is None:
        print(f"[WARNING] get_reference_replicate_for_dilution: No reference replicate mapping for {dilution}pg")
    else:
        print(f"[DEBUG] get_reference_replicate_for_dilution: {dilution}pg -> replicate {reference_replicate}")
    
    return reference_replicate

def get_reference_library_path(dilution, base_lib_path):
    """
    Get the reference library path for a specific dilution using the appropriate reference replicate.
    Format: HeLa02DDM_{dilution}pg_5x3_PyDIA_{reference_replicate}_S1-{code}_1_{number}/library.tsv
    """
    reference_replicate = get_reference_replicate_for_dilution(dilution)
    if reference_replicate is None:
        return None, None
    
    print(f"[DEBUG] get_reference_library_path: Looking for library for {dilution}pg using reference replicate {reference_replicate}")
    
    # Pattern to match the expected directory structure using the reference replicate
    pattern = f"HeLa02DDM_{dilution}pg_5x3_PyDIA_{reference_replicate}_*"
    search_path = os.path.join(base_lib_path, pattern)
    
    print(f"[DEBUG] get_reference_library_path: Searching with pattern: {search_path}")
    
    matching_dirs = glob.glob(search_path)
    print(f"[DEBUG] get_reference_library_path: Found {len(matching_dirs)} matching directories")
    
    for dir_path in matching_dirs:
        if os.path.isdir(dir_path):
            library_file = os.path.join(dir_path, "library.tsv")
            print(f"[DEBUG] get_reference_library_path: Checking for library file: {library_file}")
            if os.path.exists(library_file):
                print(f"[DEBUG] get_reference_library_path: Found reference library: {library_file}")
                return library_file, os.path.basename(dir_path)
    
    print(f"[WARNING] get_reference_library_path: No reference library found for {dilution}pg with reference replicate {reference_replicate}")
    return None, None

def process_diann_workflow(use_sbatch=True):
    """
    Process all .d directories with the DIA-NN workflow using dilution-specific reference libraries.
    All replicates of the same dilution use the same reference library.
    """
    # Store original directory to return to at the end
    original_dir = os.getcwd()
    
    # Create main diann folder
    check_create_folder("diann_masterLib")
    
    print(f"\n[DEBUG] process_diann_workflow: Starting DIA-NN workflow")
    print(f"[DEBUG] process_diann_workflow: Original directory: {original_dir}")
    print(f"[DEBUG] process_diann_workflow: Use sbatch: {use_sbatch}")

    # --- Define all paths based on the bash script ---
    main_dir = os.path.abspath(original_dir)  # Use absolute path of original directory
    print(f"[DEBUG] process_diann_workflow: Main directory: {main_dir}")
    
    # Script paths
    scripts_dir = os.path.abspath(os.path.join(main_dir, "../../src"))
    create_gpf_lib_script = os.path.join(scripts_dir, "create_gpf_lib_diann.sh")

    print(f"[DEBUG] process_diann_workflow: Scripts directory: {scripts_dir}")
    print(f"[DEBUG] process_diann_workflow: DIA-NN script: {create_gpf_lib_script} (exists: {os.path.exists(create_gpf_lib_script)})")

    # Input data and library paths
    input_folder = os.path.abspath(os.path.join(main_dir, "../../data/2025-05-UltraLowDilutions/DDM02/"))
    base_lib_path = os.path.abspath(os.path.join(main_dir, "./"))
    
    print(f"[DEBUG] process_diann_workflow: Input folder: {input_folder} (exists: {os.path.exists(input_folder)})")
    print(f"[DEBUG] process_diann_workflow: Base library path: {base_lib_path} (exists: {os.path.exists(base_lib_path)})")
    
    # DIA-NN singularity image and FASTA file paths - Fix the path construction here
    sif = os.path.abspath(os.path.join(main_dir, "../../bin/sif/2024-12-27-diann-1_9_2.sif"))
    fasta = os.path.abspath(os.path.join(main_dir, "../K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas"))
    
    print(f"[DEBUG] process_diann_workflow: DIA-NN singularity image: {sif} (exists: {os.path.exists(sif)})")
    print(f"[DEBUG] process_diann_workflow: FASTA file: {fasta} (exists: {os.path.exists(fasta)})")
    
    # --- Scan for .d directories and process each one individually ---
    workflow_basedir = os.getcwd()
    print(f"[DEBUG] process_diann_workflow: Workflow base directory: {workflow_basedir}")

    # Find all .d directories in the input folder
    d_directories = [d for d in os.listdir(input_folder) if d.endswith('.d') and os.path.isdir(os.path.join(input_folder, d))]
    print(f"\n--- Found {len(d_directories)} .d directories to process ---")
    
    # Process libraries by dilution (not by sample)
    processed_libraries = {}  # Cache for processed libraries by dilution
    
    for d_dir in d_directories:
        print(f"\n=== Processing Directory: {d_dir} ===")
        
        # Extract dilution and replicate from directory name
        sample_dilution, sample_replicate = extract_dilution_and_replicate(d_dir)
        
        if sample_dilution is None or sample_replicate is None:
            print(f"[WARNING] Could not extract dilution/replicate from {d_dir}, skipping")
            continue
            
        print(f"[DEBUG] Sample dilution: {sample_dilution}pg, replicate: {sample_replicate}")
        
        # Create folder for this sample
        sample_basename = os.path.splitext(d_dir)[0]  # Remove .d extension
        check_create_folder(sample_basename)
        
        # --- Step 1: Get the reference library for this dilution ---
        print(f"\n--- Step 1: Getting reference library for {sample_dilution}pg ---")
        
        library_key = f"{sample_dilution}pg"
        if library_key not in processed_libraries:
            reference_lib_tsv, lib_dir = get_reference_library_path(sample_dilution, base_lib_path)
            if reference_lib_tsv is None:
                print(f"[ERROR] No reference library found for {d_dir}, skipping")
                os.chdir(workflow_basedir)
                continue
            
            reference_replicate = get_reference_replicate_for_dilution(sample_dilution)
            processed_libraries[library_key] = {
                'library_tsv': reference_lib_tsv,
                'reference_replicate': reference_replicate
            }
            print(f"[DEBUG] Cached library for dilution: {library_key}")
        else:
            print(f"[DEBUG] Using cached library for dilution: {library_key}")
        
        reference_lib_tsv = processed_libraries[library_key]['library_tsv']
        reference_replicate = processed_libraries[library_key]['reference_replicate']
        print(f"[DEBUG] Using reference library: {reference_lib_tsv}")
        
        # --- Step 2: Prepare DIA-NN parameters ---
        print(f"\n--- Step 2: Running DIA-NN for {sample_basename} ---")
        
        # Generate experiment name and output library name based on the bash script logic
        exp_name = sample_basename
        
        # Extract dilution in ng format (assuming pg = ng/1000, but keeping original logic)
        dilution_ng = sample_dilution  # Keep as pg for now, adjust if needed
        
        out_lib = f"2025-06-11-lib-from-{dilution_ng}ng-rep{sample_replicate}.parquet"
        print(f"[DEBUG] Output library: {out_lib}")
        
        # DIA-NN additional parameters
        additional_param = "--direct-quant --mass-acc 15 --mass-acc-ms1 15 --report-lib-info --reannotate --full-profiling --smart-profiling"
        
        # Input .d directory path - use absolute path directly
        input_d_path = os.path.join(input_folder, d_dir)
        
        # Expected output report file
        report_file = "report.tsv"
        print(f"[DEBUG] Expected report file: {report_file}")
        
        # Print all paths for debugging
        print(f"[DEBUG] DIA-NN parameters:")
        print(f"[DEBUG]   Library: {reference_lib_tsv}")
        print(f"[DEBUG]   SIF: {sif}")
        print(f"[DEBUG]   FASTA: {fasta}")
        print(f"[DEBUG]   Output lib: {out_lib}")
        print(f"[DEBUG]   Threads: 1")
        print(f"[DEBUG]   Input: {input_d_path}")
        print(f"[DEBUG]   Additional params: {additional_param}")
        
        # Run DIA-NN
        if use_sbatch:
            check_and_run_sbatch(report_file, create_gpf_lib_script,
                                 reference_lib_tsv,  # Use absolute path directly
                                 sif,               # Use absolute path directly
                                 fasta,             # Use absolute path directly
                                 out_lib,
                                 "1",  # Thread count
                                 input_d_path,      # Use absolute path directly
                                 additional_param)
        else:
            # For direct execution, use check_and_run with the same arguments
            check_and_run(report_file, create_gpf_lib_script,
                         reference_lib_tsv,  # Use absolute path directly
                         sif,               # Use absolute path directly
                         fasta,             # Use absolute path directly
                         out_lib,
                         "1",  # Thread count
                         input_d_path,      # Use absolute path directly
                         additional_param)
        
        # Go back to workflow base
        os.chdir(workflow_basedir)
        print(f"[DEBUG] Finished processing sample {sample_basename}")
        print(f"[DEBUG] Current directory: {os.getcwd()}")

    # Go back to the original script directory
    os.chdir(original_dir)
    print(f"[DEBUG] process_diann_workflow: Returned to original directory: {os.getcwd()}")
    print("\n[DEBUG] process_diann_workflow: DIA-NN workflow processing finished.")


def main():
    print(f"[DEBUG] main: Script started")
    print(f"[DEBUG] main: Current working directory: {os.getcwd()}")
    print(f"[DEBUG] main: Command line arguments: {sys.argv}")
    
    use_sbatch = True
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["nosbatch", "no-sbatch", "direct"]:
            use_sbatch = False
            print("[DEBUG] main: Running without sbatch (direct execution).")
        elif sys.argv[1].lower() in ["sbatch", "cluster"]:
            use_sbatch = True
            print("[DEBUG] main: Running with sbatch (cluster submission).")

    print(f"[DEBUG] main: Final use_sbatch setting: {use_sbatch}")
    
    process_diann_workflow(use_sbatch=use_sbatch)
    print(f"[DEBUG] main: Script completed")

if __name__ == "__main__":
    main()
