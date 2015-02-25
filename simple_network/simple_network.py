#!/usr/bin/env python
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
synTables = {}

outputTables = {}
vmTables = {}

args = None

import os, datetime
now = datetime.datetime.now()
datadir = "_data/%s" % (now.strftime('%Y%m%d-%H%M'))
if not os.path.isdir(datadir): os.makedirs(datadir)

def make_synapse(pre, post, excitatory = True):
    #: SpikeGen detects when presynaptic Vm crosses threshold and
    #: sends out a spike event

    mu.info("Synapse (Excitatory?=%s): %s --> %s" % (excitatory, pre.path,
        post.path))
    moose.setClock(0, 1e-6)
    moose.useClock(0, pre.path, 'process')
    moose.useClock(0, post.path, 'process')
    spikegen = moose.SpikeGen('%s/spikegen' % pre.path)
    if excitatory:
        spikegen.threshold = float(args.synaptic_threshold[0])
    else:
        spikegen.threshold = float(args.synaptic_threshold[1])

    #: Create SynHandler to handle spike event input and set the
    #: activation input of synchan
    synhandler = moose.SimpleSynHandler('%s/synhandler' % post.path)
    synhandler.synapse.num = 1

    pre.connect('VmOut', spikegen, 'Vm')
    for i, syn in enumerate(synhandler.synapse):
        spikegen.connect('spikeOut', syn, 'addSpike')

    synchan = moose.SynChan('{}/synchan'.format(post.path))
    synchan.Gbar = 1e-8
    synchan.tau1, synchan.tau2 = 1e-3, 1e-3
    synchan.connect('channel', post, 'channel')

    table = moose.Table('{}/table'.format(synchan.path))
    table.connect('requestOut', synchan, 'getGk')
    synTables[synchan.path] = table


    for i in range(synhandler.synapse.num):
        synhandler.synapse[i].delay = 1e-3
        syn = synhandler.synapse[i]
        if excitatory:
            synhandler.synapse[i].weight = float(args.synaptic_weights[0])
        else:
            synhandler.synapse[i].weight = float(args.synaptic_weights[1])
    synhandler.connect('activationOut', synchan, 'activation')


def getCompType(cellPath, types=['axon']):
    comps = moose.wildcardFind('{}/##[TYPE=Compartment]'.format(cellPath))
    assert len(comps) > 0, "Cant find any compartment"
    tComps = []
    for c in comps:
        for t in types:
            if t in c.path.lower(): tComps.append(c)

    assert len(tComps) > 0, "Cant find any compartment with type %s" % type
    return random.choice(tComps)


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
        pre = getCompType(cell1, ["axon"])
        post = getCompType(cell2, ["dend", 'soma'])
        if c == 0:
            mu.info("Creating an excitatory synapse")
            make_synapse(pre, post, True)
        if c == 1:
            mu.info("Creating an inhib synapse")
            make_synapse(pre, post, False)
    
def loadCellModel(path, numCells):
    global cells
    global copyFrom

    nmlObj = nml.NeuroML()
    projDict, popDict = nmlObj.readNeuroMLFromFile(path)
    network = moose.Neutral('/network')
    network = moose.Neutral('/network')
    netList = []
    for i in range(numCells):
        cellPath = moose.Neutral('{}/cell{}'.format(network.path, i))
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
    print comps
    assert len(cells) > 1, "Check copyFrom variable %s" % copyFrom
    return cells 

def addPulseGen(c1, bursting, **kwargs):
    global simulationTime
    global inputTables, tables
    mu.info("Adding a pulse-gen to %s" % c1.path)
    pulse = moose.PulseGen('%s/pulse' % c1.path)
    pulse.level[0] = 1e-9
    if bursting:
        pulse.delay[0] = 3e-1
        pulse.width[0] = 2e-1
    else:
        pulse.delay[0] = 100e-3
        pulse.width[0] = 5e-3

    pulse.connect('output', c1, 'injectMsg')
    table = moose.Table('%s/tab' % (pulse.path))
    moose.connect(table, 'requestOut', pulse, 'getOutputValue')
    inputTables[c1.path] = table
    tables[c1.path] = table

def setRecorder(elems, filters=[]):
    global outputTables, tables
    assert len(elems) > 1, "No elements are given for setting records"
    [addTable(elem, filters)  for elem in elems]
    mu.info("Total %s recorders added" % len(outputTables))

def addTable(elem, filters, field='getVm'):
    table = None
    for f in filters:
        if f in elem.path.lower():
            table = moose.Table('{}/table'.format(elem.path))
            table.connect('requestOut', elem, field)
            tables[elem.path] = table
            outputTables[elem.path] = table
    return table

def getSoma(cell):
    comp = moose.wildcardFind('{}/#[TYPE=Compartment]'.format(cell))
    for c in comp:
        if "soma" in c.path.lower():
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

def simulate(simulationTime, solver='hsolve'):

    if solver == 'hsolve':
        solver = moose.HSolve('/hsolve')
        solver.dt = 0.5e-6
        solver.target = '/network'
        moose.reinit()

    mu.info("Simulating for %s seconds" % simulationTime)
    moose.setClock(1, 10e-6)
    moose.useClock(1, '/network/##', 'process')
    moose.reinit()

    moose.reinit()
    moose.start(simulationTime)

def plotTables():
    global outputTables
    global tables

    mu.info("Total plots %s" % len(tables))

    #mu.saveRecords(inputTables, outfile = 'data.moose')
    #mu.saveRecords(outputTables, outfile = 'soma_axon_vm.moose')

    mu.plotRecords(inputTables, outfile = 'input.png')
    mu.plotRecords(outputTables, subplot=True
            , title = "Output tables"
            , legend=True, outfile = 'comp_vm.png')
    mu.plotRecords(synTables, subplot=True, legend=True
            , title = "Synaptic tables"
            , outfile = 'synchan.png')


def plotAverage(tables):
    avgs = []
    for k in tables:
        avgs.append(tables[k].vector)
    
    clock = moose.Clock('/clock')
    yvec = np.average(avgs, axis=0)
    pylab.figure()
    pylab.plot(np.linspace(0, clock.currentTime, len(yvec)), yvec)
    pylab.title("Average activity in all somas and axons")
    pylab.xlabel("Time (sec)")
    pylab.ylabel("Vm (Volts)")
    pylab.savefig("avg_soma_axon.png")
    pylab.show()

def main():

    global totalSynapse
    global simulationTime
    global inputTables
    global tables 
    global args
    global copyFrom

    copyFrom = '/library/SampleCell'

    simulationTime = args.run_time

    modelFile = args.model_file
    loadCellModel(modelFile, args.num_cells)
    createRandomSynapse(args.num_synapse, args.excitatory_synapses)

    stimulatedNeurons = int(args.num_cells * args.stimulated_neurons)
    setupStimulus(stimulatedNeurons, args.burst_mode)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    setRecorder(comps, filters=['axon', "soma"])
    
    mu.verify()
    simulate(simulationTime)
    plotAverage(outputTables)

    #mu.writeGraphviz('network.dot')

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
    parser.add_argument('--excitatory_synapses', '-es'
        , required = True
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

    parser.add_argument('--synaptic_threshold', '-st'
            , nargs = 2
            , default = [-55e-3, -55e-3]
            , required = True
            , help = 'Synapse threshold [Excitatory, Inhibitory]'
            )

    parser.add_argument('--synaptic_weights', '-sw'
        , nargs = 2
        , default = [5e-3, -20e-3]
        , required = True
        , help = 'Synaptic weights [Excitatory, inhibitory]'
        )

    parser.add_argument('--run_time', '-rt'
        , required = True
        , type = float
        , help = 'Simulation time in seconds.'
        )

    global args
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main()
