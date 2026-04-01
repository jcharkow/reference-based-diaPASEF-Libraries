### This python library contains functions and classes for plotting and creating sampling schemes

import diapysef.timsdata as td
import sqlite3
import pandas as pd
import seaborn as sns 
from matplotlib.patches import Rectangle
from matplotlib_venn import venn2
import numpy as np


class PeptideLibrary:
    def __init__(self, pqp, name="No Name"):
        self.lib = sqlite3.connect(pqp)
        self.pre = None
        self.pep = None
        self.prot = None
        self.name = name

        query = '''select precursor.id as PREC_ID, modified_sequence, charge, protein_accession 
        from Precursor, Peptide, Protein, Peptide_protein_mapping, precursor_peptide_mapping 
        where Precursor_Peptide_mapping.Precursor_id = Precursor.id and 
        Precursor_peptide_mapping.Peptide_id = Peptide.id and 
        peptide_protein_mapping.peptide_id = Peptide.id and 
        Peptide_protein_mapping.protein_id = protein.id and 
        precursor.decoy = 0'''
        self.df = pd.read_sql(query, self.lib)
        self.df['ID'] = np.arange(0, len(self.df)) 
    
    def fetchPrecursors(self):
        if self.pre is None:
            self.pre = pd.read_sql("select id, traml_id, precursor_mz, library_rt, library_drift_time, charge from precursor where decoy == 0", self.lib)
        return self.pre

    def fetchPeptides(self):
        if self.pep is None:
            self.pep  = pd.read_sql('''select precursor_mz, library_rt, library_drift_time, modified_sequence, charge 
            from peptide, precursor_peptide_mapping, precursor where
                    precursor.id = precursor_peptide_mapping.precursor_id and 
                   peptide.id = precursor_peptide_mapping.peptide_id and 
                   precursor.decoy =0 ''', self.lib)
        return self.pep
 
    def fetchProteins(self):
        if self.prot is None:
            self.prot  = pd.read_sql('''select precursor_mz, library_rt, library_drift_time, modified_sequence, charge, protein_accession
            from peptide, precursor_peptide_mapping, precursor, protein, peptide_protein_mapping where 
                    precursor.id = precursor_peptide_mapping.precursor_id and 
                    peptide_protein_mapping.peptide_id = Peptide.id and
                    peptide_protein_mapping.protein_id = protein.id and
                    peptide.id = precursor_peptide_mapping.peptide_id and 
                    precursor.decoy =0''', self.lib)
        return self.prot

    '''get a sequence charge '''
    def sequence_charge(self):
        return set(self.df['MODIFIED_SEQUENCE'] + self.df['CHARGE'].astype(str))
        
    '''
    plot venn diagram 
    other = other PeptideLibrary Object 
    level = where comparison should occur
    **kwargs for venn2
    '''
    def plotVenn(self, other, level='precursor', **kwargs):
        if level == 'precursor':
            this_id = self.sequence_charge()
            other_id = other.sequence_charge()
        elif level == 'peptide':
            this_id = set(self.df['MODIFIED_SEQUENCE'])
            other_id = set(other.df['MODIFIED_SEQUENCE'])
        elif level == 'protein':
            this_id = set(self.df['PROTEIN_ACCESSION'])
            other_id = set(other.df['PROTEIN_ACCESSION'])
        else:
            raise Exception("Invalid Level, level must be 'precursor' or 'peptide' or 'protein'")
        return venn2([this_id, other_id], set_labels=(self.name, other.name), **kwargs)
    
   
    def graphPrecursors(self, **kwargs):
        if self.pre is None:
            self.fetchPrecursors()
        return sns.jointplot(x='PRECURSOR_MZ', y='LIBRARY_DRIFT_TIME', data=self.pre, **kwargs)

    def graphPreWindows(self, window, graph_kwargs={}, patch_kwargs={}):
        graph = self.graphPrecursors(**graph_kwargs)
        rects = window.getPatches(**patch_kwargs)
        for i in rects:
            graph.ax_joint.add_patch(i)
 
class WindowScheme:
    def __init__(self, path):
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

    # gets an array of patches
    def getPatches(self, **kwargs):
        return [ 
            Rectangle(
                (row['IsolationMz'] - row['IsolationWidth'] / 2, row['ImEnd']), 
                row['IsolationWidth'], 
                row['ImBegin'] - row['ImEnd'], **kwargs)
            for _, row in self.cycle.iterrows() ]

    def __repr__(self):
        return repr(self.cycle)


    # filter library to window scheme lib must have columns PrecursorMz and PrecursorIonMobility
    def filterLibToWindows(self, lib):

        if not 'PrecursorMz' in lib.columns:
            raise ValueError("Library must have column PrecursorMz")
        elif not 'PrecursorIonMobility' in lib.columns:
            raise ValueError("Library must have column PrecursorIonMobility")
        else:
            libWin = []
            for idx, win in self.cycle.iterrows():
                tmp = lib[(lib['PrecursorMz'].between(win['mzBegin'], win['mzEnd'])) & (lib['PrecursorIonMobility'].between(win['ImEnd'], win['ImBegin']))].copy()
                libWin.append(tmp)
            
            libWin = pd.concat(libWin)
            libWin = libWin.drop_duplicates()
            return libWin.copy()
