# This script changes the iRT space of the supplied iRT file into the supplied library. 
# Basically, this involves taking all of the peptide precursors in the iRT file and filtering the library to these peptide precursors to create a new iRT file.

import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Convert iRT file into reference library space')
parser.add_argument('irtIn', help='.tsv irt file in')
parser.add_argument('refLib', help='.tsv reference library')
parser.add_argument('irtOut', help='name of irt out file (.tsv)')

args = parser.parse_args()

# load files
irtIn = pd.read_csv(args.irtIn, sep='\t')


##### **NEW** remove the trailing '.' in unimod annotations ####
#### Only needed for this library and this iRT ####
print(irtIn['ModifiedPeptideSequence'])
irtIn['Precursor'] = irtIn['ModifiedPeptideSequence'] + irtIn['PrecursorCharge'].astype(str)

#### Replace those in reference library

libIn= pd.read_csv(args.refLib, sep='\t')
libIn['Precursor'] = libIn['ModifiedPeptideSequence'] + libIn['PrecursorCharge'].astype(str)


## filter library to irt precursors
out = libIn[libIn['Precursor'].isin(irtIn['Precursor'])]

print('iRT file contains {} Precursors'.format(len(out['Precursor'].drop_duplicates())))

out.to_csv(args.irtOut, sep='\t', index=False)
