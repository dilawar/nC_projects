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
import random
import pylab
from collections import defaultdict

totalSynapse = 0
totalCells = 0

def make_synapse(pre, post, excitatory = True):
    global totalSynapse
    synchan = moose.SynChan('{}/synchan'.format(post.path))
    synchan.Gbar = 20e-12
    synchan.tau1 = 2e-3
    synchan.tau2 = 2e-3
    synchan.connect('channel', post, 'channel')
    #: Create SynHandler to handle spike event input and set the
    #: activation input of synchan
    synhandler = moose.SimpleSynHandler('%s/synhandler' % post.path)
    synhandler.synapse.num += 1
    for i in range(synhandler.synapse.num):
        synhandler.synapse[i].delay = 5e-3
        if excitatory:
            synhandler.synapse[i].weight = 5e-3
        else:
            synhandler.synapse[i].weight = -20e-3

    synhandler.connect('activationOut', synchan, 'activation')
    #: SpikeGen detects when presynaptic Vm crosses threshold and
    #: sends out a spike event
    spikegen = moose.SpikeGen('%s/spikegen' % pre.path)
    spikegen.threshold = -1e-3
    pre.connect('VmOut', spikegen, 'Vm')
    for syn in synhandler.synapse:
        spikegen.connect('spikeOut', syn, 'addSpike')
        totalSynapse += 1
    return {'presynaptic': pre, 'postsynaptic': post, 'spikegen':
            spikegen, 'synchan': synchan, 'synhandler': synhandler}

def createRandomSynapse(cells, numsynapse, excitatory):
    print("[INFO] Creating %s synapse (%s excitatory)" % (numsynapse, excitatory))
    choices = np.random.choice([0,1], numsynapse, excitatory)
    cellPaths = cells.keys()
    assert len(cells) >= 2, "Need at least two cells for making synapse"
    for i, c in enumerate(choices):
        # Select two cells at random 
        cell1, cell2 = random.sample(cellPaths, 2)
        assert cell1 != cell2
        # select a compartment at random from each cell.
        comp1 = random.choice(cells[cell1])
        comp2 = random.choice(cells[cell2])
        assert comp1.path != comp2.path
        if c == 0:
            mu.info("Creating an excitatory synapse")
            make_synapse(comp1, comp2, True)
        if c == 1:
            mu.info("Creating an inhib synapse")
            make_synapse(comp1, comp2, False)
    
def loadCellModel(path, numCells):
    nmlObj = nml.NeuroML()
    projDict, popDict = nmlObj.readNeuroMLFromFile(path)
    network = moose.Neutral('/network')
    network = moose.Neutral('/network')
    netList = []
    for i in range(numCells):
        cellPath = moose.Neutral('{}/copy{}'.format(network.path, i))
        a = moose.copy(moose.Neutral('/library/SampleCell/'), cellPath)
    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    return comps 

def makeSynapses(comps, num_synapses, probExcitatory):
    cells = defaultdict(list)
    for c in comps:
        parent = '/'.join(c.path.split('/')[:-1])
        cells[parent].append(c)
    createRandomSynapse(cells, num_synapses, probExcitatory)
    mu.verify()

def setSimulation():
    c1 = moose.element('/network/copy0/SampleCell/Soma_0')
    pulse = moose.PulseGen('/network/pulse')
    pulse.level[0] = 1e-9
    pulse.delay[0] = 0.1
    pulse.width[0] = 40e-3
    pulse.connect('output', c1, 'injectMsg')
    table = moose.Table('%s/tab' % (pulse.path))
    moose.connect(table, 'requestOut', pulse, 'getOutputValue')
    return table

def setRecorder(elems):
    tables = []
    for elem in elems:
        table = moose.Table('{}/table'.format(elem.path))
        table.connect('requestOut', elem, 'getVm')
        tables.append(table)
    return tables

def main(args):
    global totalSynapse
    modelFile = args.cell_model
    comps = loadCellModel(modelFile, args.num_cells)
    makeSynapses(comps, args.num_synapse, args.excitatory)
    mu.writeGraphviz('network.dot')
    synchans = moose.wildcardFind('/##[TYPE=SimpleSynHandler]')
    print("++ Total %s synapses created" % totalSynapse)
    in1 = setSimulation()
    tables = setRecorder(comps)
    moose.reinit()
    moose.start(1)
    for table in tables:
        pylab.plot(table.vector)
    pylab.show()

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''A random network in moose'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--cell_model', '-f', metavar='cell_model'
            , required = True
            , type = str
            , help = 'Path of single cell model in NML'
            )
    parser.add_argument('--num_cells', '-n'
        , required = True
        , type = int
        , help = 'No of cells in network'
        )
    parser.add_argument('--num_synapse', '-s'
        , required = True
        , type = int
        , help = 'No of synapse in network'
        )
    parser.add_argument('--excitatory', '-pe'
        , required = True
        , default = 0.3
        , type = float
        , help = 'Fraction of excitatory synapses.'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main(args)
