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

def get_library_path(dilution, replicate, base_lib_path):
    """
    Get the reference library path for a specific dilution using the appropriate reference replicate.
    Format: HeLa02DDM_{dilution}pg_5x3_PyDIA_{reference_replicate}_S1-{code}_1_{number}/library.tsv
    """
    # Pattern to match the expected directory structure using the reference replicate
    pattern = f"HeLa02DDM_{dilution}pg_5x3_PyDIA_{replicate}_*"
    search_path = os.path.join(base_lib_path, pattern)
    
    print(f"[DEBUG] get_library_path: Searching with pattern: {search_path}")
    
    matching_dirs = glob.glob(search_path)
    print(f"[DEBUG] get_library_path: Found {len(matching_dirs)} matching directories")
    
    for dir_path in matching_dirs:
        if os.path.isdir(dir_path):
            library_file = os.path.join(dir_path, "library.tsv")
            print(f"[DEBUG] get_library_path: Checking for library file: {library_file}")
            if os.path.exists(library_file):
                print(f"[DEBUG] get_library_path: Found reference library: {library_file}")
                return library_file, os.path.basename(dir_path)
    
    print(f"[WARNING] get_library_path: No reference library found for {dilution}pg with reference replicate {replicate}")
    return None, None

def process_library(lib_dir, base_lib_path, sig_osw, use_sbatch=True):
    """
    Process a reference library (OpenSwathAssayGenerator -> OpenSwathDecoyGenerator -> TargetedFileConverter)
    Returns the path to the generated PQP file
    """
    print(f"[DEBUG] process_library: Processing library in {lib_dir}")
    
    original_dir = os.getcwd()
    lib_full_path = os.path.join(base_lib_path, lib_dir)
    
    if not os.path.exists(lib_full_path):
        print(f"[ERROR] process_library: Library directory does not exist: {lib_full_path}")
        return None
    
    os.chdir(lib_full_path)
    print(f"[DEBUG] process_library: Changed to library directory: {os.getcwd()}")
    
    base_lib = "library.tsv"
    if not os.path.exists(base_lib):
        print(f"[ERROR] process_library: Base library file not found: {base_lib}")
        os.chdir(original_dir)
        return None
    
    print(f"[DEBUG] process_library: Found base library: {base_lib}")
    
    # Step 1: Run OpenSwathAssayGenerator
    osw_6frags_file = base_lib.replace('.tsv', '_osw_6Frags.tsv')
    print(f"[DEBUG] process_library: Step 1 - Running OpenSwathAssayGenerator")
    print(f"[DEBUG] process_library: Expected output: {osw_6frags_file}")
    
    check_and_run(osw_6frags_file, 
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt", 
                  sig_osw, "OpenSwathAssayGenerator", 
                  "-in", base_lib, 
                  "-out", osw_6frags_file,
                  "-min_transitions", "6",
                  "-max_transitions", "6")
    
    # Step 2: Run OpenSwathDecoyGenerator
    decoys_file = base_lib.replace('.tsv', '_osw_6Frags_decoys.tsv')
    print(f"[DEBUG] process_library: Step 2 - Running OpenSwathDecoyGenerator")
    print(f"[DEBUG] process_library: Expected output: {decoys_file}")
    
    check_and_run(decoys_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "OpenSwathDecoyGenerator",
                  "-in", osw_6frags_file,
                  "-out", decoys_file,
                  "-switchKR", "true",
                  "-method", "pseudo-reverse")
    
    # Step 3: Convert to PQP
    pqp_file = base_lib.replace('.tsv', '_osw_6Frags_decoys.pqp')
    print(f"[DEBUG] process_library: Step 3 - Converting to PQP format")
    print(f"[DEBUG] process_library: Expected output: {pqp_file}")
    
    check_and_run(pqp_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "TargetedFileConverter",
                  "-in", decoys_file,
                  "-out", pqp_file)
    
    # Verify the PQP file was created and return its absolute path
    if os.path.exists(pqp_file):
        pqp_full_path = os.path.abspath(pqp_file)
        print(f"[DEBUG] process_library: Successfully created PQP file: {pqp_full_path}")
        os.chdir(original_dir)
        return pqp_full_path
    else:
        print(f"[ERROR] process_library: Failed to create PQP file: {pqp_file}")
        os.chdir(original_dir)
        return None

def generate_irt_libraries_for_dilution(scripts_path, irt_precs_path, reference_lib_tsv, dilution, sample_replicate, dilution_base_dir):
    """
    Generate iRT libraries for a specific dilution using its reference library.
    Creates one set of iRT files per dilution in a dedicated 'irts' folder within the dilution directory.
    """
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Generating iRT for {dilution}pg using reference replicate {sample_replicate}")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Reference library: {reference_lib_tsv}")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Dilution base directory: {dilution_base_dir}")
    
    original_dir = os.getcwd()
    
    # Define the path to the iRT creation script
    create_irt_script = os.path.join(scripts_path, 'create_irt_from_precs.py')
    print(f"[DEBUG] generate_irt_libraries_for_dilution: iRT creation script: {create_irt_script}")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Script exists: {os.path.exists(create_irt_script)}")
    
    if not os.path.exists(create_irt_script):
        print(f"[ERROR] generate_irt_libraries_for_dilution: iRT creation script not found!")
        return None, None
    
    # Create the irts directory within the dilution folder
    irts_dir = os.path.join(dilution_base_dir, "irts")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Creating irts directory: {irts_dir}")
    os.makedirs(irts_dir, exist_ok=True)
    
    # Change to irts directory
    os.chdir(irts_dir)
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Changed to irts directory: {os.getcwd()}")
    
    # Look for iRT precursor files that match this dilution
    irt_precursor_files = glob.glob(os.path.join(irt_precs_path, f'*{dilution}pg*.tsv'))
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Found {len(irt_precursor_files)} matching iRT precursor files")
    
    irt_lin_path = None
    irt_nonlin_path = None
    
    for irt_precs_file in irt_precursor_files:
        print(f"[DEBUG] generate_irt_libraries_for_dilution: Processing iRT file: {irt_precs_file}")
        
        # Extract iRT type from filename
        base_name = os.path.basename(irt_precs_file)
        
        if 'linIrt' in base_name:
            irt_type = 'linIrt'
        elif 'nonLinIrt' in base_name:
            irt_type = 'nonLinIrt'
        else:
            print(f"[WARNING] generate_irt_libraries_for_dilution: Could not determine iRT type from {base_name}, skipping")
            continue
        
        print(f"[DEBUG] generate_irt_libraries_for_dilution: iRT type: {irt_type}")
        
        # Construct the output file name using the reference replicate number
        out_name = f"2025-07-25-{dilution}pg-{irt_type}-diaTracerLib_rep{sample_replicate}.tsv"
        print(f"[DEBUG] generate_irt_libraries_for_dilution: Output filename: {out_name}")
        
        # Run the iRT creation
        check_and_run(out_name, 
                      "python", 
                      create_irt_script, 
                      irt_precs_file, 
                      reference_lib_tsv, 
                      out_name)
        
        # Store the paths for later use
        if irt_type == 'linIrt':
            irt_lin_path = os.path.abspath(out_name)
        elif irt_type == 'nonLinIrt':
            irt_nonlin_path = os.path.abspath(out_name)
    
    os.chdir(original_dir)
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Generated iRT libraries for {dilution}pg")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Linear iRT: {irt_lin_path}")
    print(f"[DEBUG] generate_irt_libraries_for_dilution: Non-linear iRT: {irt_nonlin_path}")
    
    return irt_lin_path, irt_nonlin_path

def process_openswath_workflow(use_sbatch=True):
    """
    Process all mzML files with the OpenSWATH workflow using dilution-specific reference libraries and iRT files.
    All replicates of the same dilution use the same reference library and iRT files.
    """
    # Store original directory to return to at the end
    original_dir = os.getcwd()
    
    # Create main osw folder
    check_create_folder("osw")
    
    print(f"\n[DEBUG] process_openswath_workflow: Starting OpenSWATH workflow")
    print(f"[DEBUG] process_openswath_workflow: Original directory: {original_dir}")
    print(f"[DEBUG] process_openswath_workflow: Use sbatch: {use_sbatch}")

    # --- Define all paths based on the bash script ---
    main_dir = os.path.abspath(original_dir)  # Use absolute path of original directory
    print(f"[DEBUG] process_openswath_workflow: Main directory: {main_dir}")
    
    # Script paths
    scripts_dir = os.path.abspath(os.path.join(main_dir, "../../src"))
    run_osw_script = os.path.join(scripts_dir, "run_osw.sh")
    run_pyprophet_export_script = os.path.join(scripts_dir, "run_pyprophet_export_parquet_scoring.sh")
    run_pyprophet_parquet_script = os.path.join(scripts_dir, "run_pyprophet_parquet.sh")
    run_pyprophet_parquet_ultrastrict_script = os.path.join(original_dir, "run_pyprophet_parquet_ultraStrict.sh")

    print(f"[DEBUG] process_openswath_workflow: Scripts directory: {scripts_dir}")
    print(f"[DEBUG] process_openswath_workflow: OSW script: {run_osw_script} (exists: {os.path.exists(run_osw_script)})")

    # Input data and library paths
    input_folder = os.path.abspath(os.path.join(main_dir, "../../data/2025-05-UltraLowDilutions/DDM02/mzML/"))
    base_lib_path = os.path.abspath(os.path.join(main_dir, "./"))
    irt_precs_path = os.path.abspath(os.path.join(main_dir, "./irtPrecs")) #TODO try with these ones first possibly have to pivot if these are not good
    
    print(f"[DEBUG] process_openswath_workflow: Input folder: {input_folder} (exists: {os.path.exists(input_folder)})")
    print(f"[DEBUG] process_openswath_workflow: Base library path: {base_lib_path} (exists: {os.path.exists(base_lib_path)})")
    print(f"[DEBUG] process_openswath_workflow: iRT precursors path: {irt_precs_path} (exists: {os.path.exists(irt_precs_path)})")
    
    # Singularity image file paths
    sig_osw = os.path.abspath(os.path.join(main_dir, "../../bin/sif/openms-executables-sif_3.2.0.sif"))
    sig_prophet = os.path.abspath(os.path.join(main_dir, "../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"))
    
    print(f"[DEBUG] process_openswath_workflow: OpenMS singularity image: {sig_osw} (exists: {os.path.exists(sig_osw)})")
    print(f"[DEBUG] process_openswath_workflow: PyProphet singularity image: {sig_prophet} (exists: {os.path.exists(sig_prophet)})")
    
    # --- Scan for samples and process each one individually ---
    workflow_basedir = os.getcwd()
    print(f"[DEBUG] process_openswath_workflow: Workflow base directory: {workflow_basedir}")

    mzml_files = glob.glob(os.path.join(input_folder, '*.mzML'))
    print(f"\n--- Found {len(mzml_files)} mzML files to process ---")
    
    # Process libraries and iRT files by dilution (not by sample)
    processed_libraries = {}  # Cache for processed PQP libraries by dilution
    processed_irt_files = {}  # Cache for processed iRT files by dilution
    dilution_base_dirs = {}   # Cache for dilution base directories
    
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
            
        print(f"\n=== Processing Sample: {output_basename} ===")
        print(f"[DEBUG] Sample dilution: {sample_dilution}pg, replicate: {sample_replicate}")
        
        # Create folder for this sample and store dilution base directory
        check_create_folder(f"{sample_dilution}pg")
        dilution_base_dir = os.getcwd()  # Store the dilution base directory
        dilution_base_dirs[f"{sample_dilution}pg"] = dilution_base_dir
        
        check_create_folder(output_basename)
        
        # --- Step 1: Get and process the reference library for this dilution ---
        print(f"\n--- Step 1: Processing reference library for {sample_dilution}pg ---")
        
        dilution_key= f"{sample_dilution}pg"
        library_key = f"{sample_dilution}pg_rep{sample_replicate}"
        if library_key not in processed_libraries:
            reference_lib_tsv, lib_dir = get_library_path(sample_dilution, sample_replicate, base_lib_path)
            if reference_lib_tsv is None:
                print(f"[ERROR] No reference library found for {output_basename}, skipping")
                os.chdir(workflow_basedir)
                continue
            
            print(f"[DEBUG] Processing new library for dilution: {library_key}")
            pqp_library_file = process_library(lib_dir, base_lib_path, sig_osw, use_sbatch)
            if pqp_library_file is None:
                print(f"[ERROR] Failed to process reference library for {output_basename}, skipping")
                os.chdir(workflow_basedir)
                continue
            
            processed_libraries[library_key] = {
                'pqp_file': pqp_library_file,
                'processed_tsv': reference_lib_tsv.replace('.tsv', '_osw_6Frags.tsv'),
            }
        else:
            print(f"[DEBUG] Using cached library for dilution: {library_key}")
        
        pqp_library_file = processed_libraries[library_key]['pqp_file']
        processed_reference_lib_tsv = processed_libraries[library_key]['processed_tsv']
        print(f"[DEBUG] Using PQP library: {pqp_library_file}")
        
        # --- Step 2: Generate iRT libraries for this dilution (if not already done) ---
        print(f"\n--- Step 2: Processing iRT libraries for {sample_dilution}pg ---")
        
        if library_key not in processed_irt_files:
            print(f"[DEBUG] Generating new iRT files for dilution: {library_key}")
            irt_lin_path, irt_nonlin_path = generate_irt_libraries_for_dilution(
                scripts_dir, irt_precs_path, processed_reference_lib_tsv, 
                sample_dilution, sample_replicate, dilution_base_dirs[dilution_key]
            )
            print(f"[DEBUG] DONE!")
            
            if irt_lin_path is None or irt_nonlin_path is None:
                print(f"[ERROR] Failed to generate iRT libraries for {sample_dilution}pg, skipping")
                os.chdir(workflow_basedir)
                continue
            
            processed_irt_files[library_key] = {
                'linear': irt_lin_path,
                'nonlinear': irt_nonlin_path
            }
        else:
            print(f"[DEBUG] Using cached iRT files for dilution: {library_key}")
            irt_lin_path = processed_irt_files[library_key]['linear']
            irt_nonlin_path = processed_irt_files[library_key]['nonlinear']
        
        print(f"[DEBUG] Using iRT libraries:")
        print(f"[DEBUG]   Linear: {irt_lin_path}")
        print(f"[DEBUG]   Non-linear: {irt_nonlin_path}")
        
        # --- Step 3: Run OSW Workflow ---
        print(f"\n--- Step 3: Running OSW workflow for {output_basename} ---")
        
        check_create_folder("oswOut")
        additional_param = "-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 300"
        
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

        # --- Step 4: Run PyProphet Export (OSW -> OSWPQ) ---
        print(f"\n--- Step 4: Running PyProphet export for {output_basename} ---")
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

        os.chdir("..") # Back to sample folder
        
        # --- Step 5: Run PyProphet XGBoost ---
        # Likely not needed because already so good
        #print(f"\n--- Step 5: Running PyProphet XGBoost for {output_basename} ---")
        oswpq_dir_path = f"oswOut/{output_basename}.oswpq"
        print(f"[DEBUG] Checking for OSWPQ directory: {oswpq_dir_path} (exists: {os.path.isdir(oswpq_dir_path)})")
        
        #if os.path.isdir(oswpq_dir_path):
            # fails on 100ng so skip
            #print("JOSH sample dilution", sample_dilution)
            #if not (sample_dilution == 100):
            #    print(f"[DEBUG] Running PyProphet XGBoost for {output_basename}")
            #    check_create_folder("pyprophet_XGB")
            #    xgb_output_file = f"{output_basename}_lib.tsv"
            #    pyprophet_args_xgb = "--classifier=XGBoost --ss_main_score=var_dotprod_score"
            #    print(f"[DEBUG] XGBoost output file: {xgb_output_file}")
            #    print(f"[DEBUG] XGBoost arguments: {pyprophet_args_xgb}")
                
            #    if use_sbatch:
            #        check_and_run_sbatch(xgb_output_file, run_pyprophet_parquet_script,
            #                             "-f", f"../oswOut/{output_basename}.oswpq",
            #                             "-a", pyprophet_args_xgb,
            #                             "-s", sig_prophet)
            #    else:
            #        check_and_run(xgb_output_file, run_pyprophet_parquet_script,
            #                             "-f", f"../oswOut/{output_basename}.oswpq",
            #                             "-a", pyprophet_args_xgb,
            #                             "-s", sig_prophet)
            #    os.chdir("..") # Back to sample folder
            #    print(f"[DEBUG] Current directory after XGBoost: {os.getcwd()}")

        # --- Step 6: Run PyProphet LDA ---
        print(f"\n--- Step 6: Running PyProphet LDA for {output_basename} ---")
        if os.path.isdir(oswpq_dir_path):
            print(f"[DEBUG] Running PyProphet LDA for {output_basename}")
            check_create_folder("pyprophet_LDA")
            lda_output_file = f"{output_basename}_lib.tsv"
            # these ones fail so get special arguments for them 
            if sample_dilution == 100:
                pyprophet_args_lda = "--classifier=LDA --pi0_lambda=0 0.001 0.0001"
                pyprophet_script=run_pyprophet_parquet_ultrastrict_script
            elif sample_dilution == 250:
                pyprophet_args_lda = "--classifier=LDA --pi0_lambda=0 0.001 0.0001"
                pyprophet_script=run_pyprophet_parquet_ultrastrict_script
            else:
                pyprophet_args_lda = "--classifier=LDA"
                pyprophet_script=run_pyprophet_parquet_script
                print(f"[DEBUG] LDA output file: {lda_output_file}")
                print(f"[DEBUG] LDA arguments: {pyprophet_args_lda}")
                
            if use_sbatch:
                check_and_run_sbatch(lda_output_file, pyprophet_script,
                                     "-f", f"../oswOut/{output_basename}.oswpq",
                                     "-a", pyprophet_args_lda,
                                     "-s", sig_prophet)
            else:
                check_and_run(lda_output_file, pyprophet_script,
                                     "-f", f"../oswOut/{output_basename}.oswpq",
                                     "-a", pyprophet_args_lda,
                                     "-s", sig_prophet)
            os.chdir("..") # Back to sample folder
            print(f"[DEBUG] Current directory after LDA: {os.getcwd()}")
        
        # Go back to dilution folder, then to workflow base
        os.chdir("..")  # Back to dilution folder
        os.chdir("..")  # Back to workflow base
        print(f"[DEBUG] Finished processing sample {output_basename}")
        print(f"[DEBUG] Current directory: {os.getcwd()}")

    # Go back to the original script directory
    os.chdir(original_dir)
    print(f"[DEBUG] process_openswath_workflow: Returned to original directory: {os.getcwd()}")
    print("\n[DEBUG] process_openswath_workflow: Dilution-specific OpenSWATH workflow processing finished.")


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
