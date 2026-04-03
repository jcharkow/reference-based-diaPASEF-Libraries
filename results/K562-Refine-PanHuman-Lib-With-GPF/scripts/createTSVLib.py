import argparse
from peptdeep.spec_lib.translate import translate_to_tsv
from peptdeep.protein.fasta import PredictSpecLibFasta
import os, psutil
import numpy as np

parser = argparse.ArgumentParser(description="Convert .HDF library to .tsv")

parser.add_argument("fIn", help='.hdf file in')
parser.add_argument("--top_k_frags", help='# fragments', default=20, required=False, type=int) # get top 20 fragments so that can ensure after OSW Library Assay generated filtering precursors are retained.

frag_inten = 0.001
min_frag_mz = 200
min_frag_nAA = 0

args = parser.parse_args()

output_tsv = f'{args.fIn[:-4]}.tsv'
print(f'Output file name: {output_tsv}')

fasta_lib = PredictSpecLibFasta(
    None,
    decoy=None
)

print("Loading .hdf ...")
fasta_lib.load_hdf(args.fIn, load_mod_seq=True)

process = psutil.Process(os.getpid())
print(f'{len(fasta_lib.precursor_df)*1e-6:.2f}M precursors with {np.prod(fasta_lib.fragment_mz_df.values.shape, dtype=float)*(1e-6):.2f}M fragments used {process.memory_info().rss/1024**3:.4f} GB memory')

fasta_lib.append_protein_name()

if 'decoy' in fasta_lib.precursor_df.columns:
    fasta_lib._precursor_df = fasta_lib.precursor_df[fasta_lib._precursor_df.decoy == 0]

print("Converting to .tsv ...")
translate_to_tsv(
    fasta_lib,
    output_tsv,
    keep_k_highest_fragments=args.top_k_frags,
    min_frag_nAA=min_frag_nAA,
    min_frag_mz=min_frag_mz,
    min_frag_intensity=frag_inten,
    batch_size=100000,
    translate_mod_dict=None,
    multiprocessing=True,
)
