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

def make_synapse(pre, post):
    synchan = moose.SynChan('{}/synchan'.format(post.path))
    synchan.Gbar = 20e-12
    synchan.tau1 = 2e-3
    synchan.tau2 = 2e-3
    synchan.connect('channel', post, 'channel')
    #: Create SynHandler to handle spike event input and set the
    #: activation input of synchan
    synhandler = moose.SimpleSynHandler('%s/synhandler' % post.path)
    synhandler.synapse.num = 1000
    synhandler.synapse[0].delay = 5e-3
    synhandler.connect('activationOut', synchan, 'activation')

    #: SpikeGen detects when presynaptic Vm crosses threshold and
    #: sends out a spike event
    spikegen = moose.SpikeGen('%s/spikegen' % pre.path)
    spikegen.threshold = -45e-3
    pre.connect('VmOut', spikegen, 'Vm')
    for syn in synhandler.synapse:
        spikegen.connect('spikeOut', syn, 'addSpike')
    return {'presynaptic': pre, 'postsynaptic': post, 'spikegen':
            spikegen, 'synchan': synchan, 'synhandler': synhandler}

def createRandomSynapse(popA, popB, numsynapse, excitory):
    compartments = popA + popB
    if not popB:
        popB = popA
    choices = np.random.choice([0,1], numsynapse, excitory)
    assert len(compartments) >= 2, compartments
    for i, c in enumerate(choices):
        # Select two compartments at random and make a synapse.
        if c == 0:
            mu.info("Creating an excitatory synapse")
            c1 = random.choice(popA)
            c2 = random.choice(popB)
            while(c1 == c2): c2 = random.choice(popB)
            make_synapse(c1, c2)
        if c == 1:
            mu.info("Creating an inhib synapse")
            c1 = random.choice(popA)
            c2 = random.choice(popB)
            while(c1 == c2): c2 = random.choice(popB)
            make_synapse(c1, c2)
    
def loadCellModel(path):
    nmlObj = nml.NeuroML()
    projDict, popDict = nmlObj.readNeuroMLFromFile(path)
    network = moose.Neutral('/network')
    network = moose.Neutral('/network')
    netList = []
    for i in range(2):
        cellPath = moose.Neutral('{}/copy{}'.format(network.path, i))
        a = moose.copy(moose.Neutral('/library/SampleCell/'), cellPath, 'SimpleCell')
    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    #createRandomSynapse(comps, (), 2, 0.3)
    c1 = comps[0]
    c2 = comps[-1]
    make_synapse(c1, c2)
    mu.writeGraphviz('network.dot')
    mu.verify()
    return comps

def setSimulation():
    c1 = moose.element('/network/copy0/SimpleCell/Soma_0')
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

def main():
    comps = loadCellModel('../simple_cell/generatedNeuroML/L3Net_11-Feb-15_16-44-37.nml1')
    in1 = setSimulation()
    tables = setRecorder(comps)
    moose.reinit()
    moose.start(1)
    for table in tables:
        pylab.plot(table.vector)
    pylab.show()

if __name__ == '__main__':
    main()
