import pandas as pd
import argparse
import numpy as np

### based on DIA-NNs internal library calibration it uses the IM from the 'IM' column and the RT from the Predicted.iRT column
### This does the same filtering wit what is done on the OpenSWATH level

def normalizeTransitionIntensities(df):
    maxIntens = max(df['Fragment.Quant.Raw'])
    df['LibraryIntensity'] = df['Fragment.Quant.Raw'] / maxIntens * 10000
    return df

def run(fIn, lib=None, noRTCalibration=False,
        noIntensityCalibration=False,
        noIMCalibration=False,
        min_fragments=4,
        columns=['Modified.Sequence',
                'Stripped.Sequence',
                'Protein.Group',
                'Precursor.Charge',
                'Fragment.Info',
                'Fragment.Quant.Raw',
                'Precursor.Id',
                'Precursor.Mz',
                'Q.Value',
                'Protein.Q.Value',
                'PG.Q.Value',
                'Global.Q.Value',
                'Global.PG.Q.Value']):

    # Load the results
    print("Reading DIA-NN results ...")

    if noRTCalibration:
        print("No RT Calibration")
        rt_column = 'iRT'
    else:
        rt_column = 'Predicted.iRT'

    # When DIA-NN outputs a library it uses the Predicted.iIM column for the IM
    # iIM is the original library IM value
    if noIMCalibration:
        print("No IM Calibration")
        im_column = 'iIM'
    else:
        im_column = 'Predicted.iIM'
    
    if noIntensityCalibration:
        print("No Intensity Calibration")
        intensity_column = "LibraryIntensity"
    else:
        intensity_column = 'Fragment.Quant.Raw'

    if noIntensityCalibration:
        rslts = pd.read_csv(fIn, sep='\t', usecols=columns + [rt_column, im_column])
    else:
        rslts = pd.read_csv(fIn, sep='\t', usecols=columns + [rt_column, im_column, intensity_column])


    rslts = rslts[(rslts['Q.Value'] <= 0.01) & 
                  (rslts['Protein.Q.Value'] <= 0.01) & 
                  (rslts['PG.Q.Value'] <= 0.01) &
                  (rslts['Global.Q.Value'] <= 0.01) & 
                  (rslts['Global.PG.Q.Value'] <= 0.01)
                 ]
    
    print(f"{len(rslts['Precursor.Id'].drop_duplicates())} Precursors in the GPF library")


    # make the transition level columns an array
    print("Fetching Fragment ion information ...")

    # Step 1: Split strings in 'Fragment.Info' and 'Fragment.Quant.Raw' only once, using more efficient methods
    fragment_info_split = rslts['Fragment.Info'].str.slice(stop=-1).str.split(';')
    fragment_quant_raw_split = rslts['Fragment.Quant.Raw'].str.slice(stop=-1).str.split(';')

    # Step 2: Concatenate the expanded DataFrames for Fragment Info and Quant Raw
    rslts = rslts.loc[np.repeat(rslts.index, fragment_info_split.str.len())].copy()

    # Step 3: Rename columns accordingly
    rslts['Fragment.Info'] = np.concatenate(fragment_info_split.values)

    # Step 5: Split the 'Fragment.Info' column into 'Annotation' and 'ProductMz'
    rslts[['Annotation', 'ProductMz']] = rslts['Fragment.Info'].str.split('/', expand=True)
    
    
    rslts['Annotation'] = rslts['Annotation'].str.replace("-unknown", '')

    if noIntensityCalibration:
        if lib is None:
            raise Exception("No Intensity Calibration requires the original library")

        if lib.endswith('zst'):
            kwargs = dict(compression='zstd')
        else:
            kwargs = dict()
        
        #### scan library to determine columns, specifically whether to use FragmentCharge or ProductCharge
        print("Loading library ...")
        lib_cols = pd.read_csv(lib, sep='\t', **kwargs, nrows=1).columns
        if 'ProductCharge' in lib_cols:
            productCharge = 'ProductCharge'
        else:
            productCharge = 'FragmentCharge'
        if 'RelativeIntensity' in lib_cols:
            libIntensity = 'RelativeIntensity'
        else:
            libIntensity = 'LibraryIntensity'
        lib = pd.read_csv(lib, sep='\t', usecols=['ModifiedPeptideSequence', 'PrecursorCharge', libIntensity, 'FragmentType', 'FragmentSeriesNumber', productCharge], **kwargs)
        import polars as pl
        lib = pl.from_pandas(lib)
        lib = lib.with_columns((pl.col('ModifiedPeptideSequence') + pl.col('PrecursorCharge').cast(pl.Utf8)).alias("Precursor"))
        lib = lib.with_columns((pl.col('FragmentType') + pl.col('FragmentSeriesNumber').cast(pl.Utf8) + '^' + pl.col(productCharge).cast(pl.Utf8)).alias('Annotation'))
        lib = lib.drop('PrecursorCharge')
        lib = lib.drop('ModifiedPeptideSequence')

        print("Merging")
        rslts = pl.from_pandas(rslts)
        rslts = rslts.join(lib, left_on=['Precursor.Id', 'Annotation'], right_on=['Precursor', 'Annotation'])

        rslts = rslts.to_pandas()


    else:
        rslts[intensity_column] = np.concatenate(fragment_quant_raw_split.values).astype(float)


        # For transitions found in multiple runs, select the one with the smallest q value
        rslts['TRANSITION_ID'] = rslts['Precursor.Id'].astype(str) + '_' + rslts['Precursor.Charge'].astype(str) + '_' + rslts['Annotation'].astype(str)
        rslts = rslts.sort_values(by='Q.Value').groupby("TRANSITION_ID").head(1)

        #assert only 1 entry per transition
        assert(len(rslts['TRANSITION_ID'].drop_duplicates()) == len(rslts)) ### Can still be duplicate transitions with different IDs

        rslts.drop(columns=['TRANSITION_ID'], inplace=True)


        print("Normalizing Intensities ... ")
        rslts[intensity_column] = (
            rslts[intensity_column] /
            rslts.groupby('Precursor.Id')[intensity_column].transform('max') *
            10000
        )

        # Drop fragments with a 0 intensity (not found in GPF)
        print("filtering precursors ...")
        rslts = rslts[rslts[intensity_column] > 0]
     
        # Drop entries with less than n transitions
        ids_to_keep = rslts[['Precursor.Id', 'Annotation']].groupby('Precursor.Id').count()
        ids_to_keep = ids_to_keep[ids_to_keep['Annotation'] >= min_fragments].index
        rslts = rslts[rslts['Precursor.Id'].isin(ids_to_keep)]
        
        print(f"after quality filtering, {len(rslts['Precursor.Id'].drop_duplicates())} precursors left")


    ### rename columns
    rslts = rslts.rename(columns={'Modified.Sequence':'ModifiedPeptideSequence', 
                                  'Stripped.Sequence':'PeptideSequence',
                                  'Protein.Group':'ProteinId', 
                                  rt_column:'NormalizedRetentionTime',
                                  im_column:'PrecursorIonMobility',
                                  intensity_column:'LibraryIntensity',
                                  'Precursor.Charge':'PrecursorCharge', 
                                  'Precursor.Mz':'PrecursorMz', 
                                  'Precursor.Id':'transition_group_id'}).drop(columns=['Fragment.Info', 'Fragment.Quant.Raw', 'Q.Value', 'Global.Q.Value', 'Global.PG.Q.Value'], errors='ignore')
    
    # add fragment columns
    rslts['FragmentCharge'] = rslts['Annotation'].str.slice(start=-1).astype(int)
    rslts['FragmentType'] = rslts['Annotation'].str.slice(stop=1)
    rslts['FragmentSeriesNumber'] = rslts['Annotation'].str.extract(r'[b,y](\d*)\^')

    return rslts


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("fIn", help='.parquet file in')
    parser.add_argument("libIn", help='.tsv file in original library')
    parser.add_argument("fOut", help='.tsv file out for library')
    parser.add_argument("--noRTCalibration", action='store_true') 
    parser.add_argument("--noIntensityCalibration", action='store_true')
    parser.add_argument("--noIMCalibration", action='store_true') 
    parser.add_argument("--min_fragments", type=int, default=4)


    args = parser.parse_args()

    rslts = run(args.fIn, noRTCalibration=args.noRTCalibration, noIntensityCalibration=args.noIntensityCalibration, noIMCalibration=args.noIMCalibration, min_fragments=args.min_fragments)

    print("writing to", args.fOut)
    rslts.to_csv(args.fOut, sep='\t', index=False)

if __name__ == "__main__":
    main()
