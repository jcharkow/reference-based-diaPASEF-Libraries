import duckdb
import argparse
import os

def process_tsv_file(input_file, output_file, min_count=6, verbose=False):
    """
    Process TSV file using DuckDB:
    1. Filter rows where precursor (ModifiedPeptideSequence + PrecursorCharge) count >= min_count
    2. Export original columns (without precursor column) to new TSV
    """
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
    
    try:
        # Connect to DuckDB (in-memory database)
        conn = duckdb.connect()
        
        if verbose:
            print(f"Processing {input_file} with minimum count {min_count}...")
        
        # Get before stats first
        before_stats_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))) as total_precursors
        FROM '{input_file}'
        """
        before_stats = conn.execute(before_stats_query).fetchone()
        
        if verbose:
            print(f"BEFORE filtering:")
            print(f"  Total rows: {before_stats[0]:,}")
            print(f"  Unique precursors: {before_stats[1]:,}")
            
            # Show precursor count distribution
            dist_query = f"""
            SELECT 
                count_per_precursor,
                COUNT(*) AS num_precursors_for_this_count
            FROM (
                SELECT 
                    CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR)) as precursor,
                    COUNT(*) as count_per_precursor
                FROM '{input_file}'
                GROUP BY CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
            ) AS precursor_counts
            GROUP BY count_per_precursor
            ORDER BY count_per_precursor
            """
            dist_results = conn.execute(dist_query).fetchall()
            print(f"  Precursor fragment ion distribution:")
            
            # The variables are adjusted to reflect the output of the reverted query.
            # 'count_per_precursor' is the number of fragment ions (e.g., 1, 2, 3...)
            # 'num_precursors_for_this_count' is the count of unique precursors that have that many fragment ions.
            for count_per_precursor, num_precursors_for_this_count in dist_results:
                ion_text = "fragment ion" if count_per_precursor == 1 else "fragment ions"
                print(f"    {num_precursors_for_this_count:,} precursors with {count_per_precursor} {ion_text}")
        
        # Execute the main filtering query
        query = f"""
        COPY (
            SELECT *
            FROM '{input_file}'
            WHERE CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR)) IN (
                SELECT CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR)) AS Precursor
                FROM '{input_file}'
                GROUP BY CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
                HAVING COUNT(*) >= {min_count}
            )
            ORDER BY ModifiedPeptideSequence, PrecursorCharge
        ) TO '{output_file}' (DELIMITER '\t', HEADER);
        """
        
        conn.execute(query)
        
        # Get after stats
        after_stats_query = f"""
        SELECT 
            COUNT(DISTINCT CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))) as filtered_precursors
        FROM '{input_file}'
        WHERE CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR)) IN (
            SELECT CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
            FROM '{input_file}'
            GROUP BY CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
            HAVING COUNT(*) >= {min_count}
        )
        """
        after_precursors = conn.execute(after_stats_query).fetchone()[0]
        
        # Get output row count
        output_count_query = f"""
        SELECT COUNT(*) 
        FROM '{input_file}'
        WHERE CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR)) IN (
            SELECT CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
            FROM '{input_file}'
            GROUP BY CONCAT(ModifiedPeptideSequence, CAST(PrecursorCharge AS VARCHAR))
            HAVING COUNT(*) >= {min_count}
        )
        """
        output_rows = conn.execute(output_count_query).fetchone()[0]
        
        conn.close()
        
        print(f"✓ Processing complete!")
        if verbose:
            print(f"AFTER filtering (≥{min_count} fragment ions):")
            print(f"  Remaining precursors: {after_precursors:,}")
            print(f"  Remaining rows: {output_rows:,}")
            print(f"  Removed precursors: {before_stats[1] - after_precursors:,}")
            print(f"  Removed rows: {before_stats[0] - output_rows:,}")
        else:
            ion_text = "fragment ion" if min_count == 1 else "fragment ions"
            print(f"  Input rows: {before_stats[0]:,}")
            print(f"  Total unique precursors: {before_stats[1]:,}")
            print(f"  Precursors with ≥{min_count} {ion_text}: {after_precursors:,}")
            print(f"  Output rows: {output_rows:,}")
        print(f"  Output file: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Process TSV file to filter precursors with count >= 6",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py data.tsv           # Creates data_filtered.tsv
  python script.py data.tsv -o results.tsv   # Creates results.tsv
  python script.py data.tsv --min-count 10   # Filter for count >= 10
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Input TSV file path'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output TSV file path (default: input_file_filtered.tsv)',
        default=None
    )
    
    parser.add_argument(
        '--min-count',
        type=int,
        default=6,
        help='Minimum count threshold for precursors (default: 6)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set output file if not specified
    if args.output is None:
        base_name = args.input_file.replace('.tsv', '')
        args.output = f"{base_name}_filtered.tsv"
    
    if args.verbose:
        print(f"Input file: {args.input_file}")
        print(f"Output file: {args.output}")
        print(f"Minimum count: {args.min_count}")
    
    success = process_tsv_file(args.input_file, args.output, args.min_count, args.verbose)
    
    if success:
        print("\n Success! Your filtered TSV file has been created.")
    else:
        print("\n Processing failed. Please check the error message above.")

if __name__ == "__main__":
    main()

