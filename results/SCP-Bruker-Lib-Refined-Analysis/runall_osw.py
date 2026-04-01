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
    dilution_match = re.search(r'(\d+)(?=pg_)', filename)
    replicate_match = re.search(r'PyDIA_(\d+)_', filename)
    
    dilution = int(dilution_match.group(1)) if dilution_match else None
    replicate = int(replicate_match.group(1)) if replicate_match else None
    
    return dilution, replicate

def get_top_replicate_for_dilution(dilution):
    """Get the top performing replicate for each dilution based on the provided table"""
    replicate_table = {
        1000: 2,
        250: 1,
        2500: 1,
        500: 3,
        5000: 2,
        100: 3
    }
    return replicate_table.get(dilution, None)

def get_library_dilution_from_id(lib_id):
    """Extract the dilution from library ID string"""
    # lib_id format: "HeLa02DDM_5000pg_5x3_PyDIA_2_S1-D8_1_1661"
    dilution_match = re.search(r'(\d+)pg_', lib_id)
    if dilution_match:
        return int(dilution_match.group(1))
    return None

def get_appropriate_libraries(sample_dilution, base_lib_path, use_only_filter=True):
    """
    Determine which libraries to use for a given sample dilution.
    Use libraries from dilutions >= sample_dilution, but only from top performing replicates.
    Skip 100pg as it's the lowest dilution (no libraries needed).
    
    This function now scans the actual directory structure to find available libraries.
    """
    available_dilutions = [100, 250, 500, 1000, 2500, 5000]
    libraries = []
    
    # Path to the osw directory containing libraries
    osw_lib_path = os.path.join(base_lib_path, "osw")
    
    if not os.path.exists(osw_lib_path):
        print(f"[WARNING] get_appropriate_libraries: OSW library path does not exist: {osw_lib_path}")
        return []
    
    # Get all available library directories
    lib_dirs = [d for d in os.listdir(osw_lib_path) if os.path.isdir(os.path.join(osw_lib_path, d))]
    print(f"[DEBUG] get_appropriate_libraries: Found {len(lib_dirs)} library directories")
    
    for lib_dilution in available_dilutions:
        if lib_dilution >= sample_dilution:
            top_replicate = get_top_replicate_for_dilution(lib_dilution)
            if top_replicate is not None:
                # Look for library directories that match this dilution and replicate
                matching_libs = []
                for lib_dir in lib_dirs:
                    # Check if this library matches the dilution and replicate we want
                    if f"{lib_dilution}pg_" in lib_dir and f"PyDIA_{top_replicate}_" in lib_dir:
                        # Verify the library file exists
                        suffix = "_lib_onlyFilter.tsv" if use_only_filter else "_lib.tsv"
                        lib_file = os.path.join(osw_lib_path, lib_dir, "pyprophet_XGB", f"{lib_dir}{suffix}")
                        if os.path.exists(lib_file):
                            matching_libs.append(lib_dir)
                            print(f"[DEBUG] get_appropriate_libraries: Found matching library: {lib_dir}")
                        else:
                            print(f"[DEBUG] get_appropriate_libraries: Library file not found for {lib_dir}: {lib_file}")
                
                if matching_libs:
                    # Use the first matching library (could add more logic here if needed)
                    libraries.append(matching_libs[0])
                    print(f"[DEBUG] get_appropriate_libraries: Using library {matching_libs[0]} for {lib_dilution}pg")
                else:
                    print(f"[WARNING] get_appropriate_libraries: No matching library found for {lib_dilution}pg replicate {top_replicate}")
    
    return libraries

def get_library_path(lib_id, base_lib_path, use_only_filter=True):
    """Get the full path to a library file"""
    suffix = "_lib_onlyFilter.tsv" if use_only_filter else "_lib.tsv"
    lib_file = os.path.join(base_lib_path, "osw", lib_id, "pyprophet_XGB", f"{lib_id}{suffix}")
    
    if not os.path.exists(lib_file):
        print(f"[WARNING] Library file not found: {lib_file}")
        return None
    
    return lib_file

def convert_tsv_to_pqp(tsv_lib_path, lib_id, pqp_libraries_dir, sig_osw, use_sbatch=True):
    """
    Convert TSV library to PQP format using OpenMS tools
    Returns the path to the generated PQP file
    """
    print(f"[DEBUG] convert_tsv_to_pqp: Converting {tsv_lib_path} to PQP format")
    print(f"[DEBUG] convert_tsv_to_pqp: Library ID: {lib_id}")
    print(f"[DEBUG] convert_tsv_to_pqp: PQP libraries directory: {pqp_libraries_dir}")
    
    # Get base filename without extension
    base_lib = f"{lib_id}.tsv"
    
    print(f"[DEBUG] convert_tsv_to_pqp: Base library name: {base_lib}")
    print(f"[DEBUG] convert_tsv_to_pqp: Working directory: {os.getcwd()}")
    
    # Step 1: Copy the library file locally
    print(f"[DEBUG] convert_tsv_to_pqp: Step 1 - Copying library file")
    if not os.path.exists(base_lib):
        try:
            import shutil
            shutil.copy2(tsv_lib_path, base_lib)
            print(f"[DEBUG] convert_tsv_to_pqp: Copied {tsv_lib_path} to {base_lib}")
        except Exception as e:
            print(f"[ERROR] convert_tsv_to_pqp: Failed to copy library file: {e}")
            return None
    else:
        print(f"[DEBUG] convert_tsv_to_pqp: Library file {base_lib} already exists")
    
    # Step 2: Run OpenSwathAssayGenerator
    osw_4_6frags_file = base_lib.replace('.tsv', '_osw_4_6Frags.tsv')
    print(f"[DEBUG] convert_tsv_to_pqp: Step 2 - Running OpenSwathAssayGenerator")
    print(f"[DEBUG] convert_tsv_to_pqp: Expected output: {osw_4_6frags_file}")
    
    check_and_run(osw_4_6frags_file, 
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt", 
                  sig_osw, "OpenSwathAssayGenerator", 
                  "-in", base_lib, 
                  "-out", osw_4_6frags_file,
                  "-min_transitions", "4",
                  "-max_transitions", "6")
    
    # Step 3: Run OpenSwathDecoyGenerator
    decoys_file = base_lib.replace('.tsv', '_osw_4_6Frags_decoys.tsv')
    print(f"[DEBUG] convert_tsv_to_pqp: Step 3 - Running OpenSwathDecoyGenerator")
    print(f"[DEBUG] convert_tsv_to_pqp: Expected output: {decoys_file}")
    
    check_and_run(decoys_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "OpenSwathDecoyGenerator",
                  "-in", osw_4_6frags_file,
                  "-out", decoys_file,
                  "-switchKR", "true",
                  "-method", "pseudo-reverse")
    
    # Step 4: Convert to PQP
    pqp_file = base_lib.replace('.tsv', '_osw_4_6Frags_decoys.pqp')
    print(f"[DEBUG] convert_tsv_to_pqp: Step 4 - Converting to PQP format")
    print(f"[DEBUG] convert_tsv_to_pqp: Expected output: {pqp_file}")
    
    check_and_run(pqp_file,
                  "apptainer", "exec", "--bind", f"{os.getcwd()}:/mnt", "--pwd", "/mnt",
                  sig_osw, "TargetedFileConverter",
                  "-in", decoys_file,
                  "-out", pqp_file)
    
    # Verify the PQP file was created
    if os.path.exists(pqp_file):
        print(f"[DEBUG] convert_tsv_to_pqp: Successfully created PQP file: {pqp_file}")
        return os.path.abspath(pqp_file)
    else:
        print(f"[ERROR] convert_tsv_to_pqp: Failed to create PQP file: {pqp_file}")
        return None

def prepare_pqp_libraries(available_libraries, base_lib_path, workflow_basedir, sig_osw, use_only_filter=True, use_sbatch=True):
    """
    Pre-convert all needed TSV libraries to PQP format once before processing samples.
    Returns a dictionary mapping library_id -> pqp_file_path
    """
    print(f"\n[DEBUG] prepare_pqp_libraries: Converting TSV libraries to PQP format")
    print(f"[DEBUG] prepare_pqp_libraries: Available libraries: {available_libraries}")
    
    # Create a directory for PQP libraries
    original_dir = os.getcwd()
    check_create_folder("pqp_libraries")
    pqp_libraries_dir = os.getcwd()
    
    pqp_library_paths = {}
    
    for lib_id in available_libraries:
        print(f"\n[DEBUG] prepare_pqp_libraries: Processing library: {lib_id}")
        
        # Get the TSV library file path
        tsv_library_file = get_library_path(lib_id, base_lib_path, use_only_filter)
        if tsv_library_file is None:
            print(f"[WARNING] prepare_pqp_libraries: Skipping library {lib_id} - TSV file not found")
            continue
        
        print(f"[DEBUG] prepare_pqp_libraries: TSV library file: {tsv_library_file}")
        
        # Convert to PQP
        pqp_file = convert_tsv_to_pqp(tsv_library_file, lib_id, pqp_libraries_dir, sig_osw, use_sbatch)
        if pqp_file is not None:
            pqp_library_paths[lib_id] = pqp_file
            print(f"[DEBUG] prepare_pqp_libraries: Successfully converted {lib_id} to PQP")
        else:
            print(f"[WARNING] prepare_pqp_libraries: Failed to convert {lib_id} to PQP")
    
    # Return to the workflow base directory
    os.chdir(original_dir)
    
    print(f"[DEBUG] prepare_pqp_libraries: PQP conversion complete. Created {len(pqp_library_paths)} PQP libraries")
    return pqp_library_paths

def generate_irt_libraries(scripts_path, irt_precs_path, pqp_libraries_dir, available_libraries, use_only_filter=True, use_sbatch=False):
    """
    Generates iRT libraries from precursor lists using the correct reference libraries from pqp_libraries.
    Creates one linear and one non-linear iRT per dilution, keeping the replicate name.
    """
    original_dir = os.getcwd()
    print(f"[DEBUG] generate_irt_libraries: Starting iRT library generation")
    print(f"[DEBUG] generate_irt_libraries: Original directory: {original_dir}")
    print(f"[DEBUG] generate_irt_libraries: Scripts path: {scripts_path}")
    print(f"[DEBUG] generate_irt_libraries: iRT precursors path: {irt_precs_path}")
    print(f"[DEBUG] generate_irt_libraries: PQP libraries directory: {pqp_libraries_dir}")
    print(f"[DEBUG] generate_irt_libraries: Available libraries: {available_libraries}")
    print(f"[DEBUG] generate_irt_libraries: Use only filter: {use_only_filter}")
    
    # Define the path to the iRT creation script
    create_irt_script = os.path.join(scripts_path, 'create_irt_from_precs.py')
    print(f"[DEBUG] generate_irt_libraries: iRT creation script: {create_irt_script}")
    print(f"[DEBUG] generate_irt_libraries: Script exists: {os.path.exists(create_irt_script)}")
    
    # Ensure the output directory for iRTs exists
    check_create_folder("irts")
    
    irt_precursor_files = glob.glob(os.path.join(irt_precs_path, '*.tsv'))
    print(f"[DEBUG] generate_irt_libraries: Found {len(irt_precursor_files)} iRT precursor files to process:")
    for i, file in enumerate(irt_precursor_files):
        print(f"[DEBUG] generate_irt_libraries:   {i+1}. {file}")

    # Create a mapping of dilution -> library_id for finding the correct reference libraries
    dilution_to_library = {}
    for lib_id in available_libraries:
        lib_dilution = get_library_dilution_from_id(lib_id)
        if lib_dilution is not None:
            dilution_to_library[lib_dilution] = lib_id
            print(f"[DEBUG] generate_irt_libraries: Mapped {lib_dilution}pg -> {lib_id}")

    for irt_precs_file in irt_precursor_files:
        print(f"\n[DEBUG] generate_irt_libraries: Processing file: {irt_precs_file}")
        
        # Extract dilution and iRT type from filename
        base_name = os.path.basename(irt_precs_file)
        print(f"[DEBUG] generate_irt_libraries: Base filename: {base_name}")
        
        # Extract dilution (e.g., "100pg" from "2025-07-25-100pg-precs-for-linIrt.tsv")
        dilution_match = re.search(r'(\d+)pg', base_name)
        if not dilution_match:
            print(f"[WARNING] generate_irt_libraries: Could not extract dilution from {base_name}, skipping")
            continue
        
        dilution = int(dilution_match.group(1))
        print(f"[DEBUG] generate_irt_libraries: Extracted dilution: {dilution}pg")
        
        # Extract iRT type (linIrt or nonLinIrt)
        if 'linIrt' in base_name:
            irt_type = 'linIrt'
        elif 'nonLinIrt' in base_name:
            irt_type = 'nonLinIrt'
        else:
            print(f"[WARNING] generate_irt_libraries: Could not determine iRT type from {base_name}, skipping")
            continue
        
        print(f"[DEBUG] generate_irt_libraries: iRT type: {irt_type}")
        
        # Find the appropriate reference library for this dilution
        if dilution not in dilution_to_library:
            print(f"[WARNING] generate_irt_libraries: No reference library found for {dilution}pg, skipping")
            continue
        
        lib_id = dilution_to_library[dilution]
        print(f"[DEBUG] generate_irt_libraries: Using reference library: {lib_id}")
        
        # Extract the replicate from the library ID to keep in the output filename
        replicate_match = re.search(r'PyDIA_(\d+)_', lib_id)
        if replicate_match:
            replicate = int(replicate_match.group(1))
        else:
            print(f"[WARNING] generate_irt_libraries: Could not extract replicate from {lib_id}, using default")
            replicate = get_top_replicate_for_dilution(dilution) or 1
        
        print(f"[DEBUG] generate_irt_libraries: Using replicate {replicate} for {dilution}pg")
        
        # Find the reference library TSV file in pqp_libraries directory
        # Format: <lib_id>_osw_4_6Frags.tsv
        reference_lib_file = os.path.join(pqp_libraries_dir, f"{lib_id}_osw_4_6Frags.tsv")
        
        if not os.path.exists(reference_lib_file):
            print(f"[WARNING] generate_irt_libraries: Reference library file not found: {reference_lib_file}")
            continue
        
        print(f"[DEBUG] generate_irt_libraries: Reference library file: {reference_lib_file}")
        
        # Construct the output file name with proper naming convention
        filter_suffix = "onlyFilter" if use_only_filter else "refined"
        out_name = f"2025-07-25-{dilution}pg-{irt_type}-BrukerLib_{filter_suffix}_rep{replicate}.tsv"
        
        print(f"[DEBUG] generate_irt_libraries: Output filename: {out_name}")
        
        # Run the iRT creation
        check_and_run(out_name, 
                      "python", 
                      create_irt_script, 
                      irt_precs_file, 
                      reference_lib_file, 
                      out_name)
    
    os.chdir(original_dir)
    print(f"[DEBUG] generate_irt_libraries: Returned to original directory: {os.getcwd()}")
    print("[DEBUG] generate_irt_libraries: iRT library generation complete.")

def process_openswath_workflow(use_sbatch=True, use_only_filter=True):
    """
    Process all mzML files with the OpenSWATH workflow using dynamic library selection.
    """
    # Store original directory to return to at the end
    original_dir = os.getcwd()
    
    # Create main osw folder with appropriate name
    folder_name = "osw_onlyFilter" if use_only_filter else "osw"
    check_create_folder(folder_name)
    
    print(f"\n[DEBUG] process_openswath_workflow: Starting OpenSWATH workflow")
    print(f"[DEBUG] process_openswath_workflow: Original directory: {original_dir}")
    print(f"[DEBUG] process_openswath_workflow: Use sbatch: {use_sbatch}")
    print(f"[DEBUG] process_openswath_workflow: Use only filter: {use_only_filter}")

    # --- Define all paths based on the bash script ---
    main_dir = os.path.abspath(original_dir)  # Use absolute path of original directory
    print(f"[DEBUG] process_openswath_workflow: Main directory: {main_dir}")
    
    # Script paths
    scripts_dir = os.path.abspath(os.path.join(main_dir, "../../src"))
    run_osw_script = os.path.join(scripts_dir, "run_osw.sh")
    run_pyprophet_export_script = os.path.join(scripts_dir, "run_pyprophet_export_parquet_scoring.sh")
    run_pyprophet_parquet_script = os.path.join(scripts_dir, "run_pyprophet_parquet.sh")
    create_irt_script = os.path.join(scripts_dir, "create_irt_from_precs.py")

    print(f"[DEBUG] process_openswath_workflow: Scripts directory: {scripts_dir}")
    print(f"[DEBUG] process_openswath_workflow: OSW script: {run_osw_script} (exists: {os.path.exists(run_osw_script)})")

    # Input data and library paths
    input_folder = os.path.abspath(os.path.join(main_dir, "../../data/2025-05-UltraLowDilutions/DDM02/mzML/"))
    base_lib_path = os.path.abspath(os.path.join(main_dir, "../../development/2025-07-28-OSW-BrukerLib-initial-attempt"))
    irt_precs_path = os.path.abspath(os.path.join(main_dir, "../../results/diaTracer-Analysis/irtPrecs"))
    
    print(f"[DEBUG] process_openswath_workflow: Input folder: {input_folder} (exists: {os.path.exists(input_folder)})")
    print(f"[DEBUG] process_openswath_workflow: Base library path: {base_lib_path} (exists: {os.path.exists(base_lib_path)})")
    print(f"[DEBUG] process_openswath_workflow: iRT precursors path: {irt_precs_path} (exists: {os.path.exists(irt_precs_path)})")
    
    # Singularity image file paths
    sig_osw = os.path.abspath(os.path.join(main_dir, "../../bin/sif/openms-executables-sif_3.2.0.sif"))
    sig_prophet = os.path.abspath(os.path.join(main_dir, "../../bin/sif/2025-08-01-pyprophet_LDA_then_XGB.sif"))
    
    print(f"[DEBUG] process_openswath_workflow: OpenMS singularity image: {sig_osw} (exists: {os.path.exists(sig_osw)})")
    print(f"[DEBUG] process_openswath_workflow: PyProphet singularity image: {sig_prophet} (exists: {os.path.exists(sig_prophet)})")
    
    # --- Step 1: Scan for samples and determine all needed libraries ---
    workflow_basedir = os.getcwd()
    print(f"[DEBUG] process_openswath_workflow: Workflow base directory: {workflow_basedir}")

    mzml_files = glob.glob(os.path.join(input_folder, '*.mzML'))
    print(f"\n--- Found {len(mzml_files)} mzML files to process ---")
    
    # Group samples by dilution and collect all needed libraries
    samples_by_dilution = defaultdict(list)
    all_needed_libraries = set()
    
    for mzml_file in mzml_files:
        # Filter out unwanted files
        if "PyDIA_R2024" in mzml_file or "-0pg" in mzml_file:
            print(f"[DEBUG] Skipping file (matches exclusion criteria): {os.path.basename(mzml_file)}")
            continue
            
        output_basename = os.path.basename(mzml_file).replace(".mzML", "")
        dilution, replicate = extract_dilution_and_replicate(output_basename)
        
        if dilution is not None:
            samples_by_dilution[dilution].append((mzml_file, output_basename))
            print(f"[DEBUG] Added {output_basename} to dilution {dilution}pg group")
            
            # Get libraries needed for this dilution
            if dilution >= 100:  # Only get libraries for dilutions above 100pg
                libs_for_dilution = get_appropriate_libraries(dilution, base_lib_path, use_only_filter)
                all_needed_libraries.update(libs_for_dilution)

    print(f"\n[DEBUG] process_openswath_workflow: All needed libraries: {sorted(all_needed_libraries)}")

    # --- Step 2: Pre-convert all needed TSV libraries to PQP format ---
    print("\n--- Converting TSV Libraries to PQP Format ---")
    pqp_library_paths = prepare_pqp_libraries(all_needed_libraries, base_lib_path, workflow_basedir, sig_osw, use_only_filter, use_sbatch)
    print("-" * 20)

    # --- Step 3: Generate iRT libraries using the correct reference libraries ---
    print("\n--- Starting iRT Library Generation ---")
    pqp_libraries_dir = os.path.join(workflow_basedir, "pqp_libraries")
    generate_irt_libraries(scripts_dir, irt_precs_path, pqp_libraries_dir, all_needed_libraries, use_only_filter)
    print("-" * 20)

    # --- Step 4: Process samples ---
    # Process each dilution group
    for dilution in sorted(samples_by_dilution.keys()):
        if dilution < 100:  # Skip 100pg and below as they don't need libraries
            print(f"[DEBUG] Skipping {dilution}pg dilution (no libraries needed for lowest concentrations)")
            continue
            
        print(f"\n--- Processing {dilution}pg dilution group ---")
        
        # Create folder for this dilution
        check_create_folder(f"{dilution}pg")
        
        # Get appropriate libraries for this dilution
        library_ids = get_appropriate_libraries(dilution, base_lib_path, use_only_filter)
        print(f"[DEBUG] Libraries for {dilution}pg: {library_ids}")
        
        # Process each sample in this dilution
        for mzml_file, output_basename in samples_by_dilution[dilution]:
            print(f"\n[DEBUG] Processing sample: {output_basename}")
            
            # Create sample folder
            check_create_folder(output_basename)
            
            # Extract dilution and replicate for the sample (for reference)
            sample_dilution, sample_replicate = extract_dilution_and_replicate(output_basename)
            print(f"[DEBUG] Sample dilution: {sample_dilution}pg, replicate: {sample_replicate}")
            
            # Process with each appropriate library
            for lib_id in library_ids:
                print(f"\n[DEBUG] Processing with library: {lib_id}")
                
                # Extract the library dilution from the library ID
                lib_dilution = get_library_dilution_from_id(lib_id)
                if lib_dilution is None:
                    print(f"[WARNING] Could not extract dilution from library ID: {lib_id}")
                    continue
                
                # Get the replicate number for this library dilution
                lib_replicate = get_top_replicate_for_dilution(lib_dilution)
                if lib_replicate is None:
                    print(f"[WARNING] Could not find replicate for library dilution: {lib_dilution}pg")
                    continue
                
                print(f"[DEBUG] Library dilution: {lib_dilution}pg, using replicate: {lib_replicate}")
                
                # Construct paths to the iRT libraries using the LIBRARY's dilution and replicate
                irt_folder_path = os.path.join(workflow_basedir, "irts")
                filter_suffix = "onlyFilter" if use_only_filter else "refined"
                irt_lin_path = os.path.join(irt_folder_path, f"2025-07-25-{lib_dilution}pg-linIrt-BrukerLib_{filter_suffix}_rep{lib_replicate}.tsv")
                irt_nonlin_path = os.path.join(irt_folder_path, f"2025-07-25-{lib_dilution}pg-nonLinIrt-BrukerLib_{filter_suffix}_rep{lib_replicate}.tsv")

                print(f"[DEBUG] Linear iRT path: {irt_lin_path} (exists: {os.path.exists(irt_lin_path)})")
                print(f"[DEBUG] Non-linear iRT path: {irt_nonlin_path} (exists: {os.path.exists(irt_nonlin_path)})")
                
                # Get the pre-converted PQP library file
                if lib_id not in pqp_library_paths:
                    print(f"[WARNING] Skipping library {lib_id} - PQP file not available")
                    continue
                
                pqp_library_file = pqp_library_paths[lib_id]
                print(f"[DEBUG] Using PQP library file: {pqp_library_file}")
                
                # Create folder for this library
                lib_folder_name = f"{lib_id}_lib"
                if use_only_filter:
                    lib_folder_name += "_onlyFilter"
                check_create_folder(lib_folder_name)
                
                # --- Run OSW Workflow ---
                print(f"[DEBUG] Starting OSW workflow for {output_basename} with {lib_id}")
                check_create_folder("oswOut")
                if use_only_filter:
                    additional_param = "-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window -1"
                else:
                    additional_param = "-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 300"

                ##### special runs:
                if (not use_only_filter) and (lib_dilution == 2500) and (sample_replicate in [3,8])  and (sample_dilution == 100):
                    print("SPECIAL!!")
                    print("Lib dilution", lib_dilution)
                    print("Sample Replicate", sample_replicate)
                    print("Sample Dilution", sample_dilution)
                    irt_lin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-linIrt-BrukerLib_refined_for_2500pg_rep_1_lib.tsv")
                    irt_nonlin_path=os.path.join(os.path.dirname(irt_lin_path), "2025-07-25-100pg-nonLinIrt-BrukerLib_refined_for_2500pg_rep_1_lib.tsv")



                
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

                # --- Run PyProphet Export (OSW -> OSWPQ) ---
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
                
                # --- Run PyProphet XGBoost ---
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
                    os.chdir("..") # Back to library folder
                    print(f"[DEBUG] Current directory after XGBoost: {os.getcwd()}")

                # --- Run PyProphet LDA ---
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
                    os.chdir("..") # Back to library folder
                    print(f"[DEBUG] Current directory after LDA: {os.getcwd()}")
                
                # Go back to sample folder
                os.chdir("..")
                print(f"[DEBUG] Finished processing library {lib_id} for {output_basename}")
            
            # Go back to dilution folder
            os.chdir("..")
            print(f"[DEBUG] Finished processing sample {output_basename}")
        
        # Go back to main workflow folder
        os.chdir("..")
        print(f"[DEBUG] Finished processing {dilution}pg dilution group")

    # Go back to the original script directory
    os.chdir(original_dir)
    print(f"[DEBUG] process_openswath_workflow: Returned to original directory: {os.getcwd()}")
    print("\n[DEBUG] process_openswath_workflow: Dynamic OpenSWATH workflow processing finished.")


def main():
    print(f"[DEBUG] main: Script started")
    print(f"[DEBUG] main: Current working directory: {os.getcwd()}")
    print(f"[DEBUG] main: Command line arguments: {sys.argv}")
    
    use_sbatch = True
    use_only_filter = True
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["nosbatch", "no-sbatch", "direct"]:
            use_sbatch = False
            print("[DEBUG] main: Running without sbatch (direct execution). Note: Some steps may require sbatch.")
        elif sys.argv[1].lower() in ["sbatch", "cluster"]:
            use_sbatch = True
            print("[DEBUG] main: Running with sbatch (cluster submission).")
        
        # Check for additional arguments
        if len(sys.argv) > 2:
            if sys.argv[2].lower() in ["nofilter", "no-filter", "regular"]:
                use_only_filter = False
                print("[DEBUG] main: Using regular libraries (not onlyFilter).")

    print(f"[DEBUG] main: Final use_sbatch setting: {use_sbatch}")
    print(f"[DEBUG] main: Final use_only_filter setting: {use_only_filter}")
    
    process_openswath_workflow(use_sbatch=use_sbatch, use_only_filter=use_only_filter)
    print(f"[DEBUG] main: Script completed")

if __name__ == "__main__":
    main()
