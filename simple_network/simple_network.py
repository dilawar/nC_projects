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
import sys
from collections import defaultdict

totalSynapse = 0
totalCells = 0
simulationTime = 0.0
cells = defaultdict(list)
tables = {}

inputTables = {}
somaTables = {}

outputTables = {}
vmTables = {}

import os, datetime
now = datetime.datetime.now()
datadir = "_data/%s" % (now.strftime('%Y%m%d-%H%M'))
if not os.path.isdir(datadir): os.makedirs(datadir)

def saveRecords(dataDict, name, plot=False, subplot=True,**kwargs):
    """Make sure that all vectors in dictionary are of same length """

    assert type(dataDict) == dict, "Got %s" % type(dataDict)

    clock = moose.Clock('/clock')
    filters = kwargs.get('filter', [])
    legend = kwargs.get('legend', False)

    global datadir
    dataFile = "%s.moose"%os.path.join(datadir, name.translate(None, '[]/'))

    mu.info("Writing data to %s" % dataFile)
    with open(dataFile, 'w') as f:
        for k in dataDict:
            yvec = dataDict[k].vector
            xvec = np.linspace(0, clock.currentTime, len(yvec))
            xline = ','.join([str(x) for x in xvec])
            yline = ','.join([str(y) for y in yvec])
            f.write('"%s:x",%s\n' % (k, xline))
            f.write('"%s:y",%s\n' % (k, yline))
    mu.info(" .. Done writing data to moose-data file")

    if not plot:
        return 

    averageData = []
    for i, k in enumerate(dataDict):
        mu.info("+ Plotting for %s" % k)
        plotThis = False
        for accept in filters:
            if accept in k: 
                plotThis = True
                break
                
        if not subplot: 
            if plotThis:
                yvec = dataDict[k].vector
                pylab.plot(xvec, yvec, label=str(k))
                averageData.append(yvec)
                if legend:
                    pylab.legend(loc='best', framealpha=0.4)
        else:
            if plotThis:
                pylab.subplot(len(dataDict), 1, i)
                yvec = dataDict[k].vector
                averageData.append(yvec)
                pylab.plot(xvec, yvec, label=str(k))
                if legend:
                    pylab.legend(loc='best', framealpha=0.4)

    pylab.title(kwargs.get('title', ''))
    pylab.ylabel(kwargs.get('ylabel', ''))
    pylab.xlabel("Time (sec)")
    pylab.figure()
    pylab.plot(xvec, np.mean(averageData, axis=0))

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

def createRandomSynapse(numsynapse, excitatory):
    print("[INFO] Creating %s synapse (%s excitatory)" % (numsynapse, excitatory))
    global cells
    choices = np.random.choice([0,1], numsynapse, p=[excitatory, 1-excitatory])
    cellPaths = cells.keys()
    if len(cells) < 2:
        print("Need at least two cells to make a synapse. Not making synapse")
        return 
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
    global cells
    nmlObj = nml.NeuroML()
    projDict, popDict = nmlObj.readNeuroMLFromFile(path)
    network = moose.Neutral('/network')
    network = moose.Neutral('/network')
    netList = []
    for i in range(numCells):
        cellPath = moose.Neutral('{}/cell{}'.format(network.path, i))
        copyFrom = '/library/SampleCell'
        try:
            a = moose.copy(moose.Neutral(copyFrom), cellPath)
        except: 
            print("Could not copy %s to %s" % (copyFrom, cellPath))
            print("Available paths are: \n")
            for p in moose.wildcardFind('/library/##'):
                print p.path
            sys.exit(0)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    for c in comps:
        parentPath = '/'.join(c.path.split('/')[:-1])
        cells[parentPath].append(c)
    return cells 

def addPulseGen(c1, bursting, **kwargs):
    global simulationTime
    mu.info("Adding a pulse-gen to %s" % c1.path)
    pulse = moose.PulseGen('%s/pulse' % c1.path)
    pulse.level[0] = 1e-9
    pulse.delay[0] = 0
    if bursting:
        pulse.width[0] = simulationTime
    else:
        pulse.delay[0] = 10e-3
        pulse.width[0] = 5e-3

    pulse.connect('output', c1, 'injectMsg')
    table = moose.Table('%s/tab' % (pulse.path))
    moose.connect(table, 'requestOut', pulse, 'getOutputValue')
    inputTables[c1.path] = table
    tables[c1.path] = table

def setRecorder(elems):
    for elem in elems:
        table = moose.Table('{}/table'.format(elem.path))
        table.connect('requestOut', elem, 'getVm')
        tables[elem.path] = table
    return tables

def getSoma(cell):
    comp = moose.wildcardFind('{}/#[TYPE=Compartment]'.format(cell))
    for c in comp:
        if "Soma" in c.path:
            return c
    return None


def setupStimulus(stimulatedNeurons, burstingNeurons):
    print("[INFO] Out of %s neurons, %s (fraction) are bursting" % (stimulatedNeurons,
        burstingNeurons))
    global cells
    choices = np.random.choice([0,1], stimulatedNeurons,
            p=[burstingNeurons,1.0-burstingNeurons]
            )
    for c in choices:
        cell = random.choice(cells.keys())
        soma = getSoma(cell)
        if c == 0:
            mu.info("A bursting neuron")
            addPulseGen(soma, bursting=True)
        else:
            mu.info("A single spiking neuron")
            addPulseGen(soma, bursting=False)

def main(args):
    global totalSynapse
    global simulationTime
    global inputTables
    global tables 
    simulationTime = args.simulation_time

    modelFile = args.model_file
    loadCellModel(modelFile, args.num_cells)
    createRandomSynapse(args.num_synapse, args.excitatory_neurons)

    stimulatedNeurons = int(args.num_cells * args.stimulated_neurons)
    setupStimulus(stimulatedNeurons, args.burst_mode)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    setRecorder(comps)

    #mu.writeGraphviz('network.dot')
    synchans = moose.wildcardFind('/##[TYPE=SimpleSynHandler]')
    print("++ Total %s synapses created" % totalSynapse)
    moose.reinit()
    mu.verify()
    mu.info("Simulating for %s seconds" % simulationTime)
    moose.start(simulationTime)
    
    mu.info("Total plots %s" % len(tables))
    saveRecords(inputTables, 'input_stim', plot=False)
    saveRecords(tables, 'compartments_vm', plot=True, subplot=False, filter=["Soma", "Axon"])
    pylab.show()

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''A random network in moose'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--model_file', '-f', metavar='model_file'
            , required = True
            , type = str
            , help = 'Path of single cell model in NML'
            )
    parser.add_argument('--num_cells', '-nc'
        , required = True
        , type = int
        , help = 'No of cells in network'
        )
    parser.add_argument('--num_synapse', '-ns'
        , required = True
        , type = int
        , help = 'No of synapse in network'
        )
    parser.add_argument('--excitatory_neurons', '-en'
        , required = True
        , default = 0.3
        , type = float
        , help = 'Fraction of excitatory synapses.'
        )
    parser.add_argument('--stimulated_neurons', '-sn'
        , required = True
        , type = float
        , help = 'Fraction of cells spiking by external input.'
        )
    parser.add_argument('--burst_mode', '-bm'
        , required = True
        , type = float
        , help = 'Fraction of stimulated neurons firing in burst mode.'
        )
    parser.add_argument('--simulation_time', '-st'
        , required = True
        , type = float
        , help = 'Simulation time in seconds.'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main(args)
