# These are python utility functions used for figure generation 

################################
########### Data Loading #######
################################
def getPrecursorSet(fPath):
    import polars as pl

    print(fPath)
    parquet = pl.scan_parquet(fPath)
    return set(parquet.filter((pl.col('SCORE_MS2.RANK') == 1) & 
                              (pl.col('SCORE_MS2.QVALUE') <= 0.01) & 
                              (pl.col('DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= 0.01) & 
                              (pl.col('SCORE_PEPTIDE.QVALUE_GLOBAL') <= 0.01))
           .with_columns((pl.col('PEPTIDE.MODIFIED_SEQUENCE') + pl.col('PRECURSOR.CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select('Precursor')
           .unique()
           .collect()    
           .to_series())


def getPrecursorSet_oswpq(fPath, cutoff=0.01):
    import polars as pl

    print(fPath)
    parquet = pl.scan_parquet(fPath + '/precursors_features.parquet')
    return set(parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('SCORE_MS2_Q_VALUE') <= cutoff) & 
                              (pl.col('PRECURSOR_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE_GLOBAL_Q_VALUE') <= cutoff))
           .with_columns((pl.col('MODIFIED_SEQUENCE') + pl.col('PRECURSOR_CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select('Precursor')
           .unique()
           .collect()    
           .to_series())


def getPrecursorSetDiann(fPath, **kwargs):
    import polars as pl

    print(fPath)
    tsv = pl.scan_csv(fPath, separator='\t', **kwargs)
    return set(tsv.filter((pl.col('Q.Value') <= 0.01) & (pl.col('Protein.Q.Value') <= 0.01))
               .select('Precursor.Id')
               .collect()
               .to_series())



def getProteinSet(fPath):
    import polars as pl

    print(fPath)
    parquet = pl.scan_parquet(fPath)
    return set(parquet.filter(
                              (pl.col('DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= 0.01))
           .select('PROTEIN.PROTEIN_ACCESSION')
           .unique()
           .collect()
           .to_series())

def getProteinSetDiann(fPath, **kwargs):
    import polars as pl

    print(fPath)
    tsv = pl.scan_csv(fPath, separator='\t', **kwargs)
    return set(tsv.filter((pl.col('Protein.Q.Value') <= 0.01) & (pl.col('PG.Q.Value') <=0.01))
               .select('Protein.Group')
               .collect()
               .to_series())


def getProteinSet_oswpq(fPath, cutoff=0.01):
    import polars as pl
    import os

    print(fPath)
    parquet = pl.scan_parquet(os.path.join(fPath, "precursors_features.parquet"))
    return set(parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('PROTEIN_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff))
           .select('PROTEIN_ACCESSION')
           .unique()
           .collect()
           .to_series())


def getPrecursorDf(fPath, suffix, cutoff=0.01, columns=['FEATURE_MS2.AREA_INTENSITY', 'SCORE_MS2.SCORE']):
    import polars as pl

    print(fPath)
    col_to_select = list(set(columns).union({'Precursor'}))
    parquet = pl.scan_parquet(fPath)
    parquet = (parquet.filter((pl.col('SCORE_MS2.RANK') == 1) & 
                              (pl.col('SCORE_MS2.QVALUE') <= cutoff) & 
                              (pl.col('DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE.QVALUE_GLOBAL') <= cutoff))
           .with_columns((pl.col('PEPTIDE.MODIFIED_SEQUENCE') + pl.col('PRECURSOR.CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select(col_to_select)
           .unique()
           .collect()
           .to_pandas())
    for i in columns:
        parquet = parquet.rename(columns={i:f'{i}_{suffix}'})
    parquet.index = parquet['Precursor']
    parquet = parquet.drop(columns='Precursor')
    return parquet


def getPrecursorDfDiann(fPath, suffix, **kwargs):
    import polars as pl 

    print(fPath)
    # Load the TSV file
    tsv = pl.scan_csv(fPath, separator='\t', **kwargs)
    # Select necessary columns
    tsv = tsv.select([
        'Precursor.Id',
        'Protein.Q.Value',
        'CScore', 
        'Q.Value', 
        'Fragment.Quant.Raw'
    ]).filter((pl.col('Q.Value') <= 0.01) & (pl.col('Protein.Q.Value') <= 0.01)).collect()
    
    # create Precursor.Quant as the sum of the raw fragment ion intensities 
    tsv = tsv.with_columns( pl.col("Fragment.Quant.Raw").str.strip_chars_end(';').str.split(";").list.eval(pl.element().cast(float)).list.sum().alias("Sum.Fragment.Quant") )  # Sum the list elements
    
    tsv = tsv.to_pandas()

    # Set Precursor.Id as the index and drop it from the columns
    tsv.index = tsv['Precursor.Id']
    tsv.drop(columns=['Precursor.Id'], inplace=True)
    
    # Add suffix to the column names
    new_columns = {col: f'{col}_{suffix}' for col in tsv.columns}
    tsv = tsv.rename(columns=new_columns)

    return tsv


def getPrecursorDf_Characteristics(fPath, cutoff=0.01, columns=['FEATURE_MS2.EXP_IM', 'FEATURE.EXP_RT', 'PRECURSOR.LIBRARY_DRIFT_TIME', 'PRECURSOR.LIBRARY_RT', 'FEATURE.DELTA_RT', 'FEATURE_MS2.DELTA_IM', 'FEATURE_MS2.VAR_LIBRARY_DOTPROD'], epsilon=0.000001):
    import polars as pl

    print(fPath)
    col_to_select = list(set(columns).union({'Precursor'}))
    parquet = pl.read_parquet(fPath)
    parquet = (parquet.filter((pl.col('SCORE_MS2.RANK') == 1) &
                              (pl.col('SCORE_MS2.QVALUE') <= cutoff) &
                              (pl.col('DECOY') == 0) &
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= cutoff) &
                              (pl.col('SCORE_PEPTIDE.QVALUE_GLOBAL') <= cutoff))
           .with_columns((pl.col('PEPTIDE.MODIFIED_SEQUENCE') + pl.col('PRECURSOR.CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select(col_to_select)
           .unique()
           .to_pandas())

    return parquet

def getPrecursorDf_Characteristics_oswpq(fPath, cutoff=0.01, columns=['FEATURE_MS2_EXP_IM', 'EXP_RT', 'PRECURSOR_LIBRARY_DRIFT_TIME', 'PRECURSOR_LIBRARY_RT', 'DELTA_RT', 'FEATURE_MS2_DELTA_IM', 'FEATURE_MS2_VAR_LIBRARY_DOTPROD'], epsilon=0.000001):
    import polars as pl
    from pathlib import Path

    print(fPath)
    if Path(fPath).suffix == '.oswpq':
        parquet = pl.read_parquet(fPath + "/precursors_features.parquet")
    else:
        parquet = pl.read_parquet(fPath)


    col_to_select = list(set(columns).union({'Precursor'}))
    parquet = (parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('SCORE_MS2_Q_VALUE') <= cutoff) & 
                              (pl.col('PRECURSOR_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE_GLOBAL_Q_VALUE') <= cutoff))
           .with_columns((pl.col('MODIFIED_SEQUENCE') + pl.col('PRECURSOR_CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select(col_to_select)
           .rename(dict(FEATURE_MS2_EXP_IM="FEATURE_MS2.EXP_IM", EXP_RT='FEATURE.EXP_RT', DELTA_RT='FEATURE.DELTA_RT', PRECURSOR_LIBRARY_RT='PRECURSOR.LIBRARY_RT', FEATURE_MS2_DELTA_IM='FEATURE_MS2.DELTA_IM', PRECURSOR_LIBRARY_DRIFT_TIME='PRECURSOR.LIBRARY_DRIFT_TIME', FEATURE_MS2_VAR_LIBRARY_DOTPROD='FEATURE_MS2.VAR_LIBRARY_DOTPROD',  ))
           .unique()
           .to_pandas()) 
    return parquet


def getPrecursorDf_Characteristics_Diann(fPath, columns=['IM', 'RT', 'iRT', 'iIM', 'Predicted.IM', 'Predicted.RT', 'Spectrum.Similarity'], **kwargs):
    import polars as pl

    print(fPath)

    # Load the TSV file
    tsv = pl.scan_csv(fPath, separator='\t', **kwargs)
    # Select necessary columns

    tsv = (tsv.filter((pl.col('Q.Value') < 0.01) & (pl.col('Protein.Q.Value') < 0.01))
           .select(columns + ['Precursor.Id']).collect())
    tsv = tsv.to_pandas()
    tsv['deltaIM'] = tsv['IM'] - tsv['Predicted.IM']
    tsv['deltaRT'] = (tsv['RT'] - tsv['Predicted.RT']) * 60
    return tsv

def getPrecursorDf_oswpq(fPath, suffix, cutoff=0.01, columns=['FEATURE_MS2_AREA_INTENSITY', 'SCORE_MS2_SCORE']):
    import polars as pl
    import pandas as pd
    import os

    print(fPath)
    col_to_select = list(set(columns).union({'Precursor'}))
    parquet = pl.scan_parquet(os.path.join(fPath,'precursors_features.parquet'))
    parquet = (parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('SCORE_MS2_Q_VALUE') <= cutoff) & 
                              (pl.col('PRECURSOR_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE_GLOBAL_Q_VALUE') <= cutoff))
           .with_columns((pl.col('MODIFIED_SEQUENCE') + pl.col('PRECURSOR_CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select(col_to_select)
           .unique()
           .collect()
           .to_pandas()) 

    parquet = parquet.rename(columns=dict(FEATURE_MS2_AREA_INTENSITY='FEATURE_MS2.AREA_INTENSITY', SCORE_MS2_SCORE='SCORE_MS2.SCORE'))
    for i in ['FEATURE_MS2.AREA_INTENSITY', 'SCORE_MS2.SCORE']:
        parquet = parquet.rename(columns={i:f'{i}_{suffix}'})
    parquet.index = parquet['Precursor']
    parquet = parquet.drop(columns='Precursor')
    return parquet


def getProteinSetDiann_matcher(fPath, **kwargs):
    import polars as pl

    print(fPath)
    # Load the TSV file
    tsv = pl.scan_csv(fPath, separator='\t', **kwargs)
    # Select necessary columns
    peptide_list = (tsv.filter((pl.col('Q.Value') < 0.01) & (pl.col('Protein.Q.Value') < 0.01))
           .select('Stripped.Sequence').unique().collect().to_series().to_list())
    return getProteinSet_helper(peptide_list)

def getProteinSet_matcher(fPath, cutoff=0.01, **kwargs):
    import polars as pl

    print(fPath)
    parquet = pl.read_parquet(fPath + "/precursors_features.parquet")
    peptide_list = (parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('SCORE_MS2_Q_VALUE') <= cutoff) & 
                              (pl.col('PRECURSOR_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE_GLOBAL_Q_VALUE') <= cutoff))
           .select('UNMODIFIED_SEQUENCE')
           .unique()
           .to_series().to_list()) 
    return getProteinSet_helper(peptide_list)

def getProteinSet_orig_matcher(fPath, cutoff=0.01, **kwargs):
    import polars as pl

    print(fPath)
    parquet = pl.read_parquet(fPath)
    peptide_list = (parquet.filter((pl.col('SCORE_MS2.RANK') == 1) & 
                              (pl.col('SCORE_MS2.QVALUE') <= cutoff) & 
                              (pl.col('DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE.QVALUE_GLOBAL') <= cutoff))
           .select('PEPTIDE.UNMODIFIED_SEQUENCE')
           .unique()
           .to_series().to_list()) 
    return getProteinSet_helper(peptide_list)

# note fasta_entires must be loaded for this function
def getProteinSet_helper(peptide_list, ):
    import pyopenms as po

    fasta = po.FASTAFile()
    fasta_entries = []
    fasta.load("../../results/K562-Library-Generation/param/2024-12-09-reviewed-contam-UP000005640.fas", fasta_entries)

    peptide_ids = []
    for seq in peptide_list:
        hit = po.PeptideHit()
        hit.setSequence(po.AASequence.fromString(seq))
        pep_id = po.PeptideIdentification()
        pep_id.setHits([hit])
        peptide_ids.append(pep_id)
    
    prot_id = po.ProteinIdentification()
    protein_ids = [prot_id]  
    # === 4. Run PeptideIndexing ===
    indexer = po.PeptideIndexing()
    params = indexer.getDefaults()
    #params.setValue("enzyme:name", "Trypsin")  
    params.setValue("decoy_string", "")     
    params.setValue("missing_decoy_action", "silent")       
    params.setValue("enzyme:specificity", "none")
    indexer.setParameters(params)
    
    # Run the mapping
    indexer.run(fasta_entries, protein_ids, peptide_ids)
    matched_accessions = set()
    
    # === 5. Extract and print mapping results ===
    for pep_id in peptide_ids:
        for hit in pep_id.getHits():
            for ev in hit.getPeptideEvidences():
                matched_accessions.add(ev.getProteinAccession())
    return matched_accessions

#########################################
## Computations and Formatting ##
#########################################

def jaccard_index(set1, set2):
    union = len(set1.union(set2)) 
    intersect = len(set1.intersection(set2))
    
    return intersect / union

# compute pairwise jaccard index
def avg_jaccard_index(rslts):
    from itertools import combinations
    count = 0 
    tot = 0
    for i, j in combinations(rslts.values(), 2):
        tot += jaccard_index(i, j)
        count += 1
    return tot / count

    
def format_ids_vs_reproducibility(df):
    import pandas as pd
    from collections import defaultdict

    avg_jaccard = defaultdict(dict)
    for lib, v in df.items():
        for cond, vv in v.items():
            avg_jaccard[lib][cond] = avg_jaccard_index(vv)

    avg_jaccard = pd.DataFrame(avg_jaccard).reset_index(names='Condition').melt(id_vars='Condition', var_name='Library', value_name='Jaccard Index')

    numIds = defaultdict(dict)
    for lib, v in df.items():
        for cond, vv in v.items():
            numIds[lib][cond] = pd.Series(list(vv.values())).apply(len).mean() 
    numIds = pd.DataFrame(numIds).reset_index(names='Condition').melt(id_vars='Condition', var_name='Library', value_name='# IDs')

    return pd.merge(numIds, avg_jaccard)

def percent_increase(initial, final):
    if initial == 0:
        raise ValueError("Initial value cannot be zero.")
    return ((final - initial) / initial) * 100


def getFeatureIDSet(fPath):
    import polars as pl

    print(fPath)
    parquet = pl.read_parquet(fPath)
    return set(parquet.filter((pl.col('SCORE_MS2.RANK') == 1) & 
                              (pl.col('SCORE_MS2.QVALUE') <= 0.01) & 
                              (pl.col('DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN.QVALUE_GLOBAL') <= 0.01) & 
                              (pl.col('SCORE_PEPTIDE.QVALUE_GLOBAL') <= 0.01))
           .with_columns((pl.col('PEPTIDE.MODIFIED_SEQUENCE') + pl.col('PRECURSOR.CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select('FEATURE_ID')
           .unique()
           .to_series())

def getFeatureIDSet_oswpq(fPath, cutoff=0.01):
    import polars as pl

    print(fPath)
    parquet = pl.read_parquet(fPath + '/precursors_features.parquet')
    return set(parquet.filter((pl.col('SCORE_MS2_PEAK_GROUP_RANK') == 1) & 
                              (pl.col('SCORE_MS2_Q_VALUE') <= cutoff) & 
                              (pl.col('PRECURSOR_DECOY') == 0) & 
                              (pl.col('SCORE_PROTEIN_GLOBAL_Q_VALUE') <= cutoff) & 
                              (pl.col('SCORE_PEPTIDE_GLOBAL_Q_VALUE') <= cutoff))
           .with_columns((pl.col('MODIFIED_SEQUENCE') + pl.col('PRECURSOR_CHARGE').cast(pl.Utf8)).alias('Precursor'))
           .select('FEATURE_ID')
           .unique()
           .to_series())


def compute_frag_intensity_residuals(parquet, osw):
    import sqlite3
    import polars as pl

    features = getFeatureIDSet(parquet)
    conn = sqlite3.connect(osw)

    df = pl.read_database("select feature_id, transition_id, area_intensity, library_intensity from feature_transition inner join transition on feature_transition.transition_id = transition.id", conn)
    df = df.filter(pl.col('FEATURE_ID').is_in(features))
    
    result = (
    df
    .with_columns([
        # Normalize FEATURE_TRANSITION_AREA_INTENSITY per feature (divide by max)
        (
            pl.col("AREA_INTENSITY") / pl.col("AREA_INTENSITY").max().over("FEATURE_ID")
        ).alias("normalized_intensity")
    ])
    .with_columns([
        # Compute residual (difference between normalized intensity and library intensity)
        (
            pl.col("normalized_intensity") - (pl.col("LIBRARY_INTENSITY") / 10000)
        ).alias("residual")
    ])
    .group_by("FEATURE_ID")
    .agg([
        pl.col("residual").sum().alias("residual")  # Sum residuals per feature
    ])
)

    return result.to_pandas()


def compute_frag_intensity_residuals_oswpq(oswpq, norm_factor=1):
    import polars as pl

    precursors = getFeatureIDSet_oswpq(oswpq)
    transitions = pl.scan_parquet(oswpq + '/transition_features.parquet') 
    transitions = transitions.select(['FEATURE_TRANSITION_AREA_INTENSITY', 'FEATURE_ID', 'TRANSITION_LIBRARY_INTENSITY', 'TRANSITION_ID']).filter(pl.col('FEATURE_ID').is_in(precursors)).collect()
    result = (
    transitions
    .with_columns([
        # Normalize FEATURE_TRANSITION_AREA_INTENSITY per feature (divide by max)
        (
            pl.col("FEATURE_TRANSITION_AREA_INTENSITY") / pl.col("FEATURE_TRANSITION_AREA_INTENSITY").max().over("FEATURE_ID")
        ).alias("normalized_intensity")
    ])
    .with_columns([
        # Compute residual (difference between normalized intensity and library intensity)
        (
            pl.col("normalized_intensity") - (pl.col("TRANSITION_LIBRARY_INTENSITY") / norm_factor)
        ).alias("residual")
    ])
    .group_by("FEATURE_ID")
    .agg([
        pl.col("residual").sum().alias("residual")  # Sum residuals per feature
    ])
)

    return result.to_pandas()



def compute_frag_intensity_residuals_diann(lib, rslts, norm_factor=10000):
    import polars as pl

    lib_pl = pl.DataFrame(lib)
    rslts_pl = pl.from_pandas(rslts)

    result = (
    rslts_pl
    .with_columns([
        # Normalize FEATURE_TRANSITION_AREA_INTENSITY per feature (divide by max)
        (
            pl.col("Fragment.Quant.Raw") / pl.col("Fragment.Quant.Raw").max().over("Precursor.Id")
        ).alias("normalized_intensity")
    ])
    .join(lib_pl, on='Fragment.Info')
    .with_columns([
        # Compute residual (difference between normalized intensity and library intensity)
        (
            pl.col("normalized_intensity") - (pl.col("LibraryIntensity") / norm_factor)
        ).alias("residual")
    ])
    .group_by("Precursor.Id")
    .agg([
        pl.col("residual").sum().alias("residual")  # Sum residuals per feature
    ])
    )

    return result.to_pandas()


def computeCVs(rslts):
    from functools import reduce
    import pandas as pd

    rslts_reduced = reduce(lambda x, y: pd.merge(x,y, left_index=True, right_index=True, how='inner'), rslts.values())

    # only fill na of intensities, other columns leave missing
    #rslts_reduced[ [f'FEATURE_MS2.AREA_INTENSITY_{i}' for i in rslts.keys() ] ] = rslts_reduced[ [f'FEATURE_MS2.AREA_INTENSITY_{i}' for i in rslts.keys() ] ].fillna(0)

    # compute CV across all
    columns = ['FEATURE_MS2.AREA_INTENSITY' + '_' + i for i in rslts.keys() ]

    rslts_reduced['cv'] = rslts_reduced[columns].std(axis=1) / rslts_reduced[columns].mean(axis=1) * 100

    return rslts_reduced
