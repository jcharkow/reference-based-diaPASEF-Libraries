import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Convert .HDF library to .tsv")

parser.add_argument("fIn", help='.hdf file in')

args = parser.parse_args()

print("Loading .tsv ...")
lib = pd.read_csv(args.fIn, sep='\t')

print("Fixing mods ...")
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Oxidation]', '(UniMod:35)', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Carbamidomethyl]', '(UniMod:4)', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Acetyl]', '(UniMod:1)', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Gln->pyro-Glu]Q', '(UniMod:28)Q', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Glu->pyro-Glu]E', '(UniMod:27)E', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Pyro-carbamidomethyl]', '(UniMod:26)', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('(UniMod:26)C(UniMod:4)', '(UniMod:26)C', regex=False)
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('[Deamidated]', '(UniMod:7)', regex=False)
#lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('(UniMod:27)C(UniMod:4)', '(UniMod:27)C', regex=False)


lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.slice(start=1, stop=-1)
## add the leading '.'
lib['ModifiedPeptide'] = lib['ModifiedPeptide'].str.replace('^\(', '.(', regex=True)

###### Rename headers 
lib = lib.rename(columns={'RT':'NormalizedRetentionTime', 'IonMobility':'PrecursorIonMobility', 'ModifiedPeptide':'ModifiedPeptideSequence', 'StrippedPeptide':'PeptideSequence', 'Genes':'GeneName', 'FragmentMz':'ProductMz', 'ProteinID':'ProteinId', 'FragmentCharge':'ProductCharge', 'FragmentNumber':'FragmentSeriesNumber'}).drop(columns='FragmentLossType')

## export 
print("Saving ...")
lib.to_csv(args.fIn[:-4] + "_fix_mods.tsv", sep='\t', index=False)
