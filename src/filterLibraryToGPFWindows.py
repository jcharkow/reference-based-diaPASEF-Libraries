# In this script we filter the library to only those that overlap with the GPF sampling scheme. This corrects for differences between the original and GPF sampling scheme, mainly errors in the GPF sampling scheme window placements.

import sqlite3
import pandas as pd
import numpy as np
import argparse

class WindowScheme:
    def __init__(self, path):
        import diapysef.timsdata as td
        if type(path) == pd.DataFrame:
            self.cycle = path
        elif path[-2:len(path)] == '.d' or path[-3:len(path)] == '.d/': # if bruker file
            exp = td.TimsData(path)
            q = exp.conn.execute("select scanNumBegin, scanNumEnd, IsolationMz, IsolationWidth from diaframemsmswindows")
            self.cycle = pd.DataFrame(q.fetchall(), columns=['ScanNumBegin', 'ScanNumEnd', 'IsolationMz', 'IsolationWidth'])
            self.cycle['ImBegin'] = exp.scanNumToOneOverK0(1, self.cycle['ScanNumBegin'])
            self.cycle['ImEnd'] = exp.scanNumToOneOverK0(1, self.cycle['ScanNumEnd'])
            #self.cycle = self.cycle.drop(columns=['ScanNumBegin', 'ScanNumEnd'])
        elif path[-4:len(path)] == '.tsv':
            self.cycle = pd.read_csv(path, '\t', columns=['IsolationMz', 'IsolationWidth', 'ImBegin', 'ImEnd'])
        
        else:
            raise Exception("Invalid path")

        self.cycle['mzBegin'] = self.cycle['IsolationMz'] - self.cycle['IsolationWidth'] / 2
        self.cycle['mzEnd'] = self.cycle['IsolationMz'] + self.cycle['IsolationWidth'] / 2

    def __repr__(self):
        return repr(self.cycle)

    def save_cycle(self, fOut):
        self.cycle.to_csv(fOut, index=False, sep='\t')


def filterLibToWindows(cycle, lib):

    if not 'PrecursorMz' in lib.columns:
        raise ValueError("Library must have column PrecursorMz")
    elif not 'PrecursorIonMobility' in lib.columns:
        raise ValueError("Library must have column PrecursorIonMobility")
    else:
        libWin = []
        for idx, win in cycle.iterrows():
            tmp = lib[(lib['PrecursorMz'].between(win['mzBegin'], win['mzEnd'])) & (lib['PrecursorIonMobility'].between(win['ImEnd'], win['ImBegin']))].copy()
            libWin.append(tmp)
        
        libWin = pd.concat(libWin)
        libWin = libWin.drop_duplicates()
        return libWin.copy()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Filter library to windows from a cycle file"
    )
    parser.add_argument(
        "--cycle",
        required=True,
        type=str,
        help="Path to cycle file (CSV or TSV)"
    )
    parser.add_argument(
        "--library",
        required=True,
        type=str,
        help="Path to library file (CSV or TSV)"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Path to output filtered library file"
    )
    
    args = parser.parse_args()
    
    # Load cycle and library
    cycle = pd.read_csv(args.cycle, sep='\t')
    lib = pd.read_csv(args.library, sep='\t' )
    
    # Filter library to windows
    filtered_lib = filterLibToWindows(cycle, lib)
    
    # Write output
    filtered_lib.to_csv(args.output, index=False)
    print(f"Filtered library written to {args.output}")
    print(f"Original library size: {len(lib)} rows")
    print(f"Filtered library size: {len(filtered_lib)} rows")
