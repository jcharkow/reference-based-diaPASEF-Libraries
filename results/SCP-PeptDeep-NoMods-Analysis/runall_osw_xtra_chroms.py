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

check_create_folder("osw_xtraChroms")
check_create_folder("HeLa02DDM_500pg_5x3_PyDIA_1_S1-C10_1_1642")


check_and_run_sbatch('HeLa02DDM_500pg_5x3_PyDIA_1_S1-C10_1_1642.osw',
              '../../src/run_osw_tsv.sh',
              '../../data/2025-05-UltraLowDilutions/DDM02/mzML/HeLa02DDM_500pg_5x3_PyDIA_1_S1-C10_1_1642.mzML',
              '../PeptDeep-NoMods-Analysis/2025-11-04-filtered-lib-based-on-500pg-rep-1-silico.tsv.zst',
              'formattedLib/2025-07-25-500pg-precs-for-linIrt-PeptDeepNoModsLib.tsv', 
              'formattedLib/2025-07-25-500pg-precs-for-nonLinIrt-PeptDeepNoModsLib.tsv', 
              'HeLa02DDM_500pg_5x3_PyDIA_1_S1-C10_1_1642',
              'True', 
              '../../bin/sif/2024-12-13-OSW-TSV-Lib.sif', 
              '-irt_im_extraction_window 0.2 -ion_mobility_window 0.06 -rt_extraction_window 500')
