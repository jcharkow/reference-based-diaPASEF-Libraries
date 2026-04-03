import pandas as pd
import argparse
from sklearn import preprocessing

def run(fIn, noRTCalibration=False, 
        noIMCalibration=False, 
        min_fragments =4, 
        noIntensityCalibration=False, 
        peptide_protein_filter=True, 
        columns=[
            'PRECURSOR.PRECURSOR_MZ', 
            'TRANSITION.PRODUCT_MZ', 
            'TRANSITION.CHARGE', 
            'TRANSITION.TYPE', 
            'TRANSITION.ORDINAL', 
            'PROTEIN.PROTEIN_ACCESSION', 
            'PEPTIDE.MODIFIED_SEQUENCE', 
            'PEPTIDE.UNMODIFIED_SEQUENCE', 
            'PRECURSOR.CHARGE', 
            'SCORE_MS2.QVALUE', 
            'DECOY', 
            'SCORE_PROTEIN.QVALUE_GLOBAL', 
            'SCORE_PEPTIDE.QVALUE_GLOBAL',
            'PRECURSOR_ID',
            'SCORE_MS2.RANK',
            'TRANSITION_ID',
            'PRECURSOR.GROUP_LABEL']):

    if noRTCalibration:
        print("No RT Calibration")
        rt_column = 'PRECURSOR.LIBRARY_RT'
    else:
        rt_column = 'FEATURE.EXP_RT'

    if noIMCalibration:
        print("No IM Calibration")
        im_column = 'PRECURSOR.LIBRARY_DRIFT_TIME'
    else:
        im_column = 'FEATURE_MS2.EXP_IM'

    if noIntensityCalibration:
        print("No Intensity Calibration")
        intensity_column = 'TRANSITION.LIBRARY_INTENSITY'
    else:
        intensity_column = 'FEATURE_TRANSITION.AREA_INTENSITY'

    # Load the results
    print("Reading parquet")
    oswRslts = pd.read_parquet(fIn, columns=columns + [rt_column, im_column, intensity_column])
    print("Complete parquet loading")

    # Filter to "candidates" for the library
    if peptide_protein_filter:
        oswRslts = (oswRslts[
            (oswRslts['SCORE_MS2.QVALUE'] < 0.01) &
            (oswRslts['SCORE_PROTEIN.QVALUE_GLOBAL'] < 0.01) &
            (oswRslts['SCORE_PEPTIDE.QVALUE_GLOBAL'] < 0.01) &
            (oswRslts['SCORE_MS2.RANK'] == 1) & 
            (oswRslts['DECOY'] == 0)])
    else:
        oswRslts = (oswRslts[
            (oswRslts['SCORE_MS2.QVALUE'] < 0.01) &
            (oswRslts['SCORE_MS2.RANK'] == 1) & 
            (oswRslts['DECOY'] == 0)])



    oswRslts = oswRslts.sort_values(by='SCORE_MS2.QVALUE').groupby("TRANSITION_ID").head(1) ## for precursors found in more than one run, select the one with the smallest q value

    #assert only 1 entry per transition
    assert(len(oswRslts['TRANSITION_ID'].drop_duplicates()) == len(oswRslts)) ### Can still be duplicate transitions with different IDs


    if not noRTCalibration:
        # normalize Retention time to between 0-100
        oswRslts[rt_column] = preprocessing.MinMaxScaler().fit_transform(oswRslts[[rt_column]]) * 100

    if not noIntensityCalibration:
        # normalize intensity of fragment ions 
        print("Normalizing Intensities ... ")

        oswRslts[intensity_column] = (
                oswRslts[intensity_column] /
                oswRslts.groupby('PRECURSOR_ID')[intensity_column].transform('max') *
                10000
            )

    oswRslts = oswRslts.rename(columns={'PRECURSOR.PRECURSOR_MZ':'PrecursorMz', 
                                        'TRANSITION.PRODUCT_MZ':'ProductMz', 
                                        'PROTEIN.PROTEIN_ACCESSION':'ProteinId', 
                                        rt_column:'NormalizedRetentionTime',
                                        im_column:'PrecursorIonMobility',
                                        intensity_column:'LibraryIntensity',
                                        'PEPTIDE.UNMODIFIED_SEQUENCE':'PeptideSequence', 
                                        'PEPTIDE.MODIFIED_SEQUENCE':'ModifiedPeptideSequence', 
                                        'PRECURSOR.CHARGE':'PrecursorCharge', 
                                        'PRECURSOR.GROUP_LABEL':'PeptideGroupLabel'})

    # Add annotation column
    oswRslts['Annotation'] = oswRslts['TRANSITION.TYPE'] + oswRslts['TRANSITION.ORDINAL'].astype(str) + "^" + oswRslts['TRANSITION.CHARGE'].astype(str)
    
    # Drop fragments with a 0 intensity (not found in GPF)
    oswRslts = oswRslts[oswRslts['LibraryIntensity'] > 0]
    
    # Drop entries with less than n transitions
    ids_to_keep = oswRslts[['PRECURSOR_ID', 'Annotation']].groupby('PRECURSOR_ID').count()
    ids_to_keep = ids_to_keep[ids_to_keep['Annotation'] >= min_fragments].index
    oswRslts = oswRslts[oswRslts['PRECURSOR_ID'].isin(ids_to_keep)]
    
    oswRslts = oswRslts.drop(columns=['PRECURSOR_ID', 
                                      'TRANSITION_ID', 
                                      'DECOY', 
                                      'SCORE_MS2.RANK', 
                                      'SCORE_PROTEIN.QVALUE_GLOBAL', 
                                      'SCORE_PEPTIDE.QVALUE_GLOBAL', 
                                      'SCORE_MS2.QVALUE', 
                                      'TRANSITION.TYPE', 
                                      'TRANSITION.ORDINAL', 
                                      'TRANSITION.CHARGE'])


    

    return oswRslts


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("fIn", help='.parquet file in')
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
