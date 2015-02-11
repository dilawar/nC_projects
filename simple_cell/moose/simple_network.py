"""simple_cell.py: 

    A simple cell constructed by neuroconstruct. Loading in MOOSE.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import moose
import moose.utils as mu
import moose.neuroml as nml
import numpy as np

def createRandomSynapse(compartments, numsynapse, excitory):
    choices = np.random.choice([0,1], numsynapse, excitory)
    for c in choices:
        if c == 0:
            pass
        if c == 1:
            pass

def loadCellModel(path):
    nmlObj = nml.NeuroML()
    projDict, popDict = nmlObj.readNeuroMLFromFile(path)
    network = moose.Neutral('/network')
    network = moose.Neutral('/network')
    netList = []
    for i in range(100):
        cellPath = moose.Neutral('{}/copy{}'.format(network.path, i))
        a = moose.copy(moose.Neutral('/library/SampleCell/'), cellPath, 'SimpleCell')
    comps = moose.wildcardFind('{}/##[TYPE=Compartment]')
    createRandomSynapse(comps, connectivity=5, excitory=0.3)
    mu.writeGraphviz('network.dot')
    mu.verify()

def main():
    loadCellModel('../generatedNeuroML/L3Net_11-Feb-15_16-44-37.nml1')


if __name__ == '__main__':
    main()
