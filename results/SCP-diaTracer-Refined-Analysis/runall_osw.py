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

def extract_dilution_and_replicate(filename):
    """Extract dilution and replicate from filename"""
    dilution_match = re.search(r'(\d+)pg_', filename)
    replicate_match = re.search(r'PyDIA_(\d+)_', filename)
    
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

def get_applicable_library_dilutions(sample_dilution):
    """
    Get list of library dilutions that should be used for a given sample dilution.
    Returns libraries from sample_dilution and higher concentrations.
    """
    available_dilutions = [250, 500, 1000, 2500, 5000]
    applicable_dilutions = [d for d in available_dilutions if d > sample_dilution]
    
    print(f"[DEBUG] get_applicable_library_dilutions: For {sample_dilution}pg sample, using libraries: {applicable_dilutions}")
    return applicable_dilutions

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

def process_reference_library(lib_dir, base_lib_path, sig_osw, use_sbatch=True):
    """
    Process a reference library (OpenSwathAssayGenerator -> OpenSwathDecoyGenerator -> TargetedFileConverter)
    Uses 6 transitions as per the second script
    Returns the path to the generated PQP file
    """
    print(f"[DEBUG] process_reference_library: Processing library in {lib_dir}")
    
    original_dir = os.getcwd()
    lib_full_path = os.path.join(base_lib_path, lib_dir)
    
    if not os.path.exists(lib_full_path):
        print(f"[ERROR] process_reference_library: Library directory does not exist: {lib_full_path}")
        return None
    
    os.chdir(lib_full_path)
    print(f"[DEBUG] process_reference_library: Changed to library directory: {os.getcwd()}")
    
    base_lib = "library.tsv"
    if not os.path.exists(base_lib):
        print(f"[ERROR] process_reference_library: Base library file not found: {base_lib}")
        os.chdir(original_dir)
        return None
    
    print(f"[DEBUG] process_reference_library: Found base library: {base_lib}")
    
    # Step 1: Run OpenSwathAssayGenerator (6 transitions for diaTracer libraries)
    osw_6frags_file = base_lib.replace('.tsv', '_osw_6Frags.tsv')
    print(f"[DEBUG] process_reference_library: Step 1 - Running OpenSwathAssayGenerator")
    print(f"[DEBUG] process_reference_library: Expected output: {osw_6frags_file}")
    
    check_and_run(osw_6frags_file, 
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt", 
                  sig_osw, "OpenSwathAssayGenerator", 
                  "-in", base_lib, 
                  "-out", osw_6frags_file,
                  "-min_transitions", "6",
                  "-max_transitions", "6")
    
    # Step 2: Run OpenSwathDecoyGenerator
    decoys_file = base_lib.replace('.tsv', '_osw_6Frags_decoys.tsv')
    print(f"[DEBUG] process_reference_library: Step 2 - Running OpenSwathDecoyGenerator")
    print(f"[DEBUG] process_reference_library: Expected output: {decoys_file}")
    
    check_and_run(decoys_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "OpenSwathDecoyGenerator",
                  "-in", osw_6frags_file,
                  "-out", decoys_file,
                  "-switchKR", "true",
                  "-method", "pseudo-reverse")
    
    # Step 3: Convert to PQP
    pqp_file = base_lib.replace('.tsv', '_osw_6Frags_decoys.pqp')
    print(f"[DEBUG] process_reference_library: Step 3 - Converting to PQP format")
    print(f"[DEBUG] process_reference_library: Expected output: {pqp_file}")
    
    check_and_run(pqp_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "TargetedFileConverter",
                  "-in", decoys_file,
                  "-out", pqp_file)
    
    # Verify the PQP file was created and return its absolute path
    if os.path.exists(pqp_file):
        pqp_full_path = os.path.abspath(pqp_file)
        print(f"[DEBUG] process_reference_library: Successfully created PQP file: {pqp_full_path}")
        os.chdir(original_dir)
        return pqp_full_path
    else:
        print(f"[ERROR] process_reference_library: Failed to create PQP file: {pqp_file}")
        os.chdir(original_dir)
        return None

def get_existing_irt_files(base_lib_path, dilution, reference_replicate):
    """
    Find existing iRT files for a given dilution and reference replicate.
    Files should already exist, so we just need to locate them.
    Expected path structure: ../diaTracer-Analysis/osw_masterLib/{dilution}pg/irts/
    Expected file pattern: *{dilution}pg-linIrt-diaTracerLib_rep{reference_replicate}.tsv
    """
    print(f"[DEBUG] get_existing_irt_files: Looking for iRT files for {dilution}pg, replicate {reference_replicate}")
    
    # Construct the correct directory path
    irt_dir = os.path.join(base_lib_path, "osw_masterLib", f"{dilution}pg", "irts")
    print(f"[DEBUG] get_existing_irt_files: iRT directory: {irt_dir}")
    print(f"[DEBUG] get_existing_irt_files: Directory exists: {os.path.exists(irt_dir)}")
    
    if not os.path.exists(irt_dir):
        print(f"[ERROR] get_existing_irt_files: iRT directory does not exist: {irt_dir}")
        return None, None
    
    # Look for iRT files with the correct naming pattern
    irt_lin_pattern = os.path.join(irt_dir, f"*{dilution}pg-linIrt-diaTracerLib_rep{reference_replicate}.tsv")
    irt_nonlin_pattern = os.path.join(irt_dir, f"*{dilution}pg-nonLinIrt-diaTracerLib_rep{reference_replicate}.tsv")
    
    print(f"[DEBUG] get_existing_irt_files: Linear iRT pattern: {irt_lin_pattern}")
    print(f"[DEBUG] get_existing_irt_files: Non-linear iRT pattern: {irt_nonlin_pattern}")
    
    irt_lin_files = glob.glob(irt_lin_pattern)
    irt_nonlin_files = glob.glob(irt_nonlin_pattern)
    
    print(f"[DEBUG] get_existing_irt_files: Found {len(irt_lin_files)} linear iRT files")
    print(f"[DEBUG] get_existing_irt_files: Found {len(irt_nonlin_files)} non-linear iRT files")
    
    # List all files found for debugging
    if irt_lin_files:
        for file in irt_lin_files:
            print(f"[DEBUG] get_existing_irt_files: Linear iRT file: {file}")
    if irt_nonlin_files:
        for file in irt_nonlin_files:
            print(f"[DEBUG] get_existing_irt_files: Non-linear iRT file: {file}")
    
    irt_lin_path = irt_lin_files[0] if irt_lin_files else None
    irt_nonlin_path = irt_nonlin_files[0] if irt_nonlin_files else None
    
    if irt_lin_path:
        print(f"[DEBUG] get_existing_irt_files: Using linear iRT: {irt_lin_path}")
    else:
        print(f"[WARNING] get_existing_irt_files: No linear iRT file found for {dilution}pg replicate {reference_replicate}")
        # List all files in the directory for debugging
        if os.path.exists(irt_dir):
            all_files = os.listdir(irt_dir)
            print(f"[DEBUG] get_existing_irt_files: All files in {irt_dir}:")
            for file in all_files:
                print(f"[DEBUG]   {file}")
    
    if irt_nonlin_path:
        print(f"[DEBUG] get_existing_irt_files: Using non-linear iRT: {irt_nonlin_path}")
    else:
        print(f"[WARNING] get_existing_irt_files: No non-linear iRT file found for {dilution}pg replicate {reference_replicate}")
    
    return irt_lin_path, irt_nonlin_path

def process_openswath_workflow(use_sbatch=True):
    """
    Process all mzML files with the OpenSWATH workflow using multiple reference libraries.
    Each sample uses libraries from its dilution and all higher dilution concentrations.
    """
    # Store original directory to return to at the end
    original_dir = os.getcwd()
    
    # Create main osw folder
    check_create_folder("osw")
    
    print(f"\n[DEBUG] process_openswath_workflow: Starting OpenSWATH workflow with multiple diaTracer libraries")
    print(f"[DEBUG] process_openswath_workflow: Original directory: {original_dir}")
    print(f"[DEBUG] process_openswath_workflow: Use sbatch: {use_sbatch}")

    # --- Define all paths ---
    main_dir = os.path.abspath(original_dir)
    print(f"[DEBUG] process_openswath_workflow: Main directory: {main_dir}")
    
    # Script paths
    scripts_dir = os.path.abspath(os.path.join(main_dir, "../../src"))
    run_osw_script = os.path.join(scripts_dir, "run_osw.sh")
    run_pyprophet_export_script = os.path.join(scripts_dir, "run_pyprophet_export_parquet_scoring.sh")
    run_pyprophet_parquet_script = os.path.join(scripts_dir, "run_pyprophet_parquet.sh")

    print(f"[DEBUG] process_openswath_workflow: Scripts directory: {scripts_dir}")
    print(f"[DEBUG] process_openswath_workflow: OSW script: {run_osw_script} (exists: {os.path.exists(run_osw_script)})")

    # Input data and library paths - updated for diaTracer libraries
    input_folder = os.path.abspath(os.path.join(main_dir, "../../data/2025-05-UltraLowDilutions/DDM02/mzML/"))
    base_lib_path = os.path.abspath(os.path.join(main_dir, "../diaTracer-Analysis/"))  
    
    print(f"[DEBUG] process_openswath_workflow: Input folder: {input_folder} (exists: {os.path.exists(input_folder)})")
    print(f"[DEBUG] process_openswath_workflow: Base library path: {base_lib_path} (exists: {os.path.exists(base_lib_path)})")
    
    # Singularity image file paths
    sig_osw = os.path.abspath(os.path.join(main_dir, "../../bin/sif/openms-executables-sif_3.2.0.sif"))
    sig_prophet = os.path.abspath(os.path.join(main_dir, "../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"))
    
    print(f"[DEBUG] process_openswath_workflow: OpenMS singularity image: {sig_osw} (exists: {os.path.exists(sig_osw)})")
    print(f"[DEBUG] process_openswath_workflow: PyProphet singularity image: {sig_prophet} (exists: {os.path.exists(sig_prophet)})")
    
    # --- Scan for samples and process each one with multiple libraries ---
    workflow_basedir = os.getcwd()
    print(f"[DEBUG] process_openswath_workflow: Workflow base directory: {workflow_basedir}")

    mzml_files = glob.glob(os.path.join(input_folder, '*.mzML'))
    print(f"\n--- Found {len(mzml_files)} mzML files to process ---")
    
    # Process libraries and iRT files by dilution (not by sample)
    processed_libraries = {}  # Cache for processed PQP libraries by dilution
    processed_irt_files = {}  # Cache for processed iRT files by dilution
    
    # Group samples by dilution for better organization
    samples_by_dilution = defaultdict(list)
    
    for mzml_file in mzml_files:
        # Filter out unwanted files
        if "PyDIA_R2024" in mzml_file or "_0pg" in mzml_file:
            print(f"[DEBUG] Skipping file (matches exclusion criteria): {os.path.basename(mzml_file)}")
            continue
            
        output_basename = os.path.basename(mzml_file).replace(".mzML", "")
        sample_dilution, sample_replicate = extract_dilution_and_replicate(output_basename)
        
        if sample_dilution is None or sample_replicate is None:
            print(f"[WARNING] Could not extract dilution/replicate from {output_basename}, skipping")
            continue
        
            
        samples_by_dilution[sample_dilution].append((mzml_file, output_basename, sample_replicate))
    
    # Process each dilution group
    for sample_dilution in sorted(samples_by_dilution.keys()):
        print(f"\n=== Processing {sample_dilution}pg dilution group ===")
        
        # Create folder for this dilution
        check_create_folder(f"{sample_dilution}pg")
        dilution_base_dir = os.getcwd()
        
        # Get applicable library dilutions for this sample dilution
        library_dilutions = get_applicable_library_dilutions(sample_dilution)
        
        # Pre-process all needed libraries for this sample dilution
        for lib_dilution in library_dilutions:
            library_key = f"{lib_dilution}pg"
            if library_key not in processed_libraries:
                print(f"\n--- Processing reference library for {lib_dilution}pg ---")
                reference_lib_tsv, lib_dir = get_reference_library_path(lib_dilution, base_lib_path)
                if reference_lib_tsv is None:
                    print(f"[ERROR] No reference library found for {lib_dilution}pg, skipping")
                    continue
                
                print(f"[DEBUG] Processing new library for dilution: {library_key}")
                pqp_library_file = process_reference_library(lib_dir, base_lib_path, sig_osw, use_sbatch)
                if pqp_library_file is None:
                    print(f"[ERROR] Failed to process reference library for {lib_dilution}pg, skipping")
                    continue
                
                reference_replicate = get_reference_replicate_for_dilution(lib_dilution)
                processed_libraries[library_key] = {
                    'pqp_file': pqp_library_file,
                    'processed_tsv': reference_lib_tsv.replace('.tsv', '_osw_6Frags.tsv'),
                    'reference_replicate': reference_replicate
                }
                
                # Also get iRT files for this library dilution
                irt_lin_path, irt_nonlin_path = get_existing_irt_files(base_lib_path, lib_dilution, reference_replicate)
                if irt_lin_path and irt_nonlin_path:
                    processed_irt_files[library_key] = {
                        'linear': irt_lin_path,
                        'nonlinear': irt_nonlin_path
                    }
                else:
                    print(f"[ERROR] Failed to find iRT libraries for {lib_dilution}pg")
                    
        # Process each sample in this dilution group
        for mzml_file, output_basename, sample_replicate in samples_by_dilution[sample_dilution]:
            print(f"\n=== Processing Sample: {output_basename} ===")
            print(f"[DEBUG] Sample dilution: {sample_dilution}pg, replicate: {sample_replicate}")
            
            check_create_folder(output_basename)
            
            # Process sample with each applicable library
            for lib_dilution in library_dilutions:
                library_key = f"{lib_dilution}pg"
                
                if library_key not in processed_libraries or library_key not in processed_irt_files:
                    print(f"[WARNING] Skipping library {library_key} - not available")
                    continue
                
                print(f"\n--- Processing {output_basename} with {lib_dilution}pg library ---")
                
                # Create folder for this library
                lib_folder_name = f"lib_{lib_dilution}pg"
                check_create_folder(lib_folder_name)
                
                # Get library and iRT file paths
                pqp_library_file = processed_libraries[library_key]['pqp_file']
                irt_lin_path = processed_irt_files[library_key]['linear']
                irt_nonlin_path = processed_irt_files[library_key]['nonlinear']
                
                print(f"[DEBUG] Using PQP library: {pqp_library_file}")
                print(f"[DEBUG] Using iRT libraries:")
                print(f"[DEBUG]   Linear: {irt_lin_path}")
                print(f"[DEBUG]   Non-linear: {irt_nonlin_path}")
                
                # --- Step 1: Run OSW Workflow ---
                print(f"\n--- Step 1: Running OSW workflow for {output_basename} with {lib_dilution}pg library ---")
                
                check_create_folder("oswOut")
                additional_param = "-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 300"
                 ##### special runs:
                if (lib_dilution == 2500) and (sample_dilution == 100):
                    print("SPECIAL!!")
                    print("Lib dilution", lib_dilution)
                    print("Sample Replicate", sample_replicate)
                    print("Sample Dilution", sample_dilution)
                    irt_lin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-linIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv")
                    irt_nonlin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-nonLinIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv")
                if (lib_dilution == 500) and (sample_dilution == 100):
                    print("SPECIAL!!")
                    print("Lib dilution", lib_dilution)
                    print("Sample Replicate", sample_replicate)
                    print("Sample Dilution", sample_dilution)
                    irt_lin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-linIrt-diaTracerLib_refined_for_500pg_rep_3_lib.tsv")
                    irt_nonlin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-nonLinIrt-diaTracerLib_refined_for_500pg_rep_3_lib.tsv")
                if (lib_dilution == 2500) and (sample_dilution == 250) and (sample_replicate == 7):
                    print("SPECIAL!!")
                    print("Lib dilution", lib_dilution)
                    print("Sample Replicate", sample_replicate)
                    print("Sample Dilution", sample_dilution)
                    irt_lin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-250pg-linIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv")
                    irt_nonlin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-250pg-nonLinIrt-diaTracerLib_refined_for_2500pg_rep_3_lib.tsv")






               
                osw_output_file = f"{output_basename}.osw"
                print(f"[DEBUG] Expected OSW output file: {osw_output_file}")
                
                if use_sbatch:
                    check_and_run_sbatch(osw_output_file, run_osw_script, 
                                         mzml_file, pqp_library_file, irt_lin_path, irt_nonlin_path, 
                                         output_basename, "False", sig_osw, additional_param)
                else:
                    check_and_run(osw_output_file, run_osw_script, 
                                         mzml_file, pqp_library_file, irt_lin_path, irt_nonlin_path, 
                                         output_basename, "False", sig_osw, additional_param)

                # --- Step 2: Run PyProphet Export (OSW -> OSWPQ) ---
                print(f"\n--- Step 2: Running PyProphet export for {output_basename} ---")
                print(f"[DEBUG] Checking for OSW file: {osw_output_file} (exists: {os.path.exists(osw_output_file)})")
                
                if os.path.exists(osw_output_file):
                    oswpq_output_dir = f"{output_basename}.oswpq"
                    print(f"[DEBUG] Expected OSWPQ output directory: {oswpq_output_dir}")
                    
                    func = check_and_run_sbatch if use_sbatch else check_and_run
                    # The report file for this step is a directory, so we check for its existence
                    if not os.path.isdir(oswpq_output_dir):
                        print(f"[DEBUG] Running PyProphet export for {output_basename}")
                        func(oswpq_output_dir, run_pyprophet_export_script, 
                                        "-f", osw_output_file, 
                                        "-s", sig_prophet)
                    else:
                        print(f"[DEBUG] Output directory {oswpq_output_dir} already exists, skipping export.")
                else:
                    print(f"[WARNING] OSW file {osw_output_file} not found, skipping PyProphet steps")

                os.chdir("..") # Back to library folder
                
                # --- Step 3: Run PyProphet XGBoost ---
                print(f"\n--- Step 3: Running PyProphet XGBoost for {output_basename} ---")
                oswpq_dir_path = f"oswOut/{output_basename}.oswpq"
                print(f"[DEBUG] Checking for OSWPQ directory: {oswpq_dir_path} (exists: {os.path.isdir(oswpq_dir_path)})")
                
                if os.path.isdir(oswpq_dir_path):
                    print(f"[DEBUG] Running PyProphet XGBoost for {output_basename}")
                    check_create_folder("pyprophet_XGB")
                    xgb_output_file = f"{output_basename}_lib.tsv"
                    pyprophet_args_xgb = "--classifier=XGBoost --ss_main_score=var_dotprod_score"
                    print(f"[DEBUG] XGBoost output file: {xgb_output_file}")
                    print(f"[DEBUG] XGBoost arguments: {pyprophet_args_xgb}")
                    
                    if use_sbatch:
                        check_and_run_sbatch(xgb_output_file, run_pyprophet_parquet_script,
                                             "-f", f"../oswOut/{output_basename}.oswpq",
                                             "-a", pyprophet_args_xgb,
                                             "-s", sig_prophet)
                    else:
                        check_and_run(xgb_output_file, run_pyprophet_parquet_script,
                                             "-f", f"../oswOut/{output_basename}.oswpq",
                                             "-a", pyprophet_args_xgb,
                                             "-s", sig_prophet)
                    os.chdir("..") # Back to library folder
                    print(f"[DEBUG] Current directory after XGBoost: {os.getcwd()}")

                # --- Step 4: Run PyProphet LDA ---
                print(f"\n--- Step 4: Running PyProphet LDA for {output_basename} ---")
                if os.path.isdir(oswpq_dir_path):
                    print(f"[DEBUG] Running PyProphet LDA for {output_basename}")
                    check_create_folder("pyprophet_LDA")
                    lda_output_file = f"{output_basename}_lib.tsv"
                    pyprophet_args_lda = "--classifier=LDA"
                    print(f"[DEBUG] LDA output file: {lda_output_file}")
                    print(f"[DEBUG] LDA arguments: {pyprophet_args_lda}")
                    
                    if use_sbatch:
                        check_and_run_sbatch(lda_output_file, run_pyprophet_parquet_script,
                                             "-f", f"../oswOut/{output_basename}.oswpq",
                                             "-a", pyprophet_args_lda,
                                             "-s", sig_prophet)
                    else:
                        check_and_run(lda_output_file, run_pyprophet_parquet_script,
                                             "-f", f"../oswOut/{output_basename}.oswpq",
                                             "-a", pyprophet_args_lda,
                                             "-s", sig_prophet)
                    os.chdir("..") # Back to library folder
                    print(f"[DEBUG] Current directory after LDA: {os.getcwd()}")
                
                # Go back to sample folder
                os.chdir("..")  
                print(f"[DEBUG] Finished processing {output_basename} with {lib_dilution}pg library")
            
            # Go back to dilution folder
            os.chdir("..")  
            print(f"[DEBUG] Finished processing sample {output_basename}")
        
        # Go back to workflow base
        os.chdir("..")  
        print(f"[DEBUG] Finished processing {sample_dilution}pg dilution group")

    # Go back to the original script directory
    os.chdir(original_dir)
    print(f"[DEBUG] process_openswath_workflow: Returned to original directory: {os.getcwd()}")
    print("\n[DEBUG] process_openswath_workflow: Multi-library diaTracer OpenSWATH workflow processing finished.")


def main():
    print(f"[DEBUG] main: Script started")
    print(f"[DEBUG] main: Current working directory: {os.getcwd()}")
    print(f"[DEBUG] main: Command line arguments: {sys.argv}")
    
    use_sbatch = True
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["nosbatch", "no-sbatch", "direct"]:
            use_sbatch = False
            print("[DEBUG] main: Running without sbatch (direct execution). Note: Some steps may require sbatch.")
        elif sys.argv[1].lower() in ["sbatch", "cluster"]:
            use_sbatch = True
            print("[DEBUG] main: Running with sbatch (cluster submission).")

    print(f"[DEBUG] main: Final use_sbatch setting: {use_sbatch}")
    
    process_openswath_workflow(use_sbatch=use_sbatch)
    print(f"[DEBUG] main: Script completed")

if __name__ == "__main__":
    main()
