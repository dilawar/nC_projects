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

spikeTables = {}
timeVec = None

args = None

import os, datetime
now = datetime.datetime.now()
datadir = "_data/%s" % (now.strftime('%Y%m%d-%H%M'))
if not os.path.isdir(datadir): os.makedirs(datadir)

moose.setClock(7, 1000)

def deactivateSomas(comps):
    global args
    init, totalFraction = args.deactivated_somas
    total = int(args.num_cells * totalFraction)
    mu.info("Deactivating %s somas" % total)
    somas = []
    for c in comps:
        if "soma" in c.path.lower(): somas.append(c.path)
    
    mu.info("Deactivating total %s somas" % total)
    _deactivateSomas = set(random.sample(somas, total))
    assert len(_deactivateSomas) == total, "Expected %s somas to be deactivated" % total
    for cpath in _deactivateSomas:
        moose.Compartment(cpath).initVm = init
        moose.useClock(7, cpath, 'process')
        moose.useClock(7, cpath, 'init')

def make_synapse(pre, post, excitatory = True):
    #: SpikeGen detects when presynaptic Vm crosses threshold and
    #: sends out a spike event

    #mu.info("Synapse (Excitatory?=%s): %s --> %s" % (excitatory, pre.path,
        #post.path))
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

def count_spikes(tables, threshold):
    '''Count the number of spikes, also pupulate the spikeTables '''
    nSpikes = 0
    spikeBegin = False
    spikeEnds = False
    clock = moose.Clock('/clock')
    for tname in tables:
        t = tables[tname]
        dt = clock.currentTime / len(t.vector)
        spikeList = []
        for i, x in enumerate(t.vector):
            if x > threshold:
                if not spikeBegin:
                    spikeBegin = True
                    spikeEnds = False
                else: pass
            else:
                if spikeBegin:
                    spikeEnds = True
                    spikeBegin = False
                    spikeList.append(i*dt)
                    nSpikes += 1
        spikeTables[tname] = spikeList
    return nSpikes


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
    #print("[INFO] Creating %s synapse (%s excitatory)" % (numsynapse, excitatory))
    global cells
    excitatoryS, inhibS = 0, 0
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
            #mu.info("Creating an excitatory synapse")
            make_synapse(pre, post, True)
            excitatoryS += 1
        if c == 1:
            #mu.info("Creating an inhib synapse")
            make_synapse(pre, post, False)
            inhibS +=1 
    mu.info("Syanpses: Exc: %s, Inh: %s" % (excitatoryS, inhibS))
    
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
            mu.warn("Could not copy %s to %s" % (copyFrom, cellPath))
            mu.info("Available paths are: \n")
            for p in moose.wildcardFind('/library/##'):
                print p.path
            sys.exit(0)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    for c in comps:
        parentPath = '/'.join(c.path.split('/')[:-1])
        cells[parentPath].append(c)
    assert len(cells) > 1, "Check copyFrom variable %s" % copyFrom
    return cells 

def addPulseGen(c1, bursting, **kwargs):
    global simulationTime
    global inputTables, tables

    global args

    freq, width, height = args.input
    delay = (1.0 / float(freq)) - float(width)
    assert delay > 0.0, "Wrong value %s" % args.input

    pulse = moose.PulseGen('%s/pulse' % c1.path)
    pulse.level[0] = float(height)
    if bursting:
        pulse.delay[0] = 4e-1
        pulse.width[0] = 3e-1
    else:
        pulse.delay[0] = delay
        pulse.width[0] = float(width)

    pulse.connect('output', c1, 'injectMsg')
    table = moose.Table('%s/tab' % (pulse.path))
    moose.connect(table, 'requestOut', pulse, 'getOutputValue')
    inputTables[c1.path] = table
    tables[c1.path] = table

def setRecorder(elems, filters=[], total = 0):
    assert len(elems) > 1, "No elements are given for setting records"
    out = []
    for el in elems:
        for f in filters:
            if f.lower() in el.path.lower(): out.append(el)

    [addTable(o)  for o in out]
    mu.info("Total %s recorders added" % len(outputTables))

def addTable(elem, field='getVm'):
    global outputTables, tables
    table = None
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
    mu.info("Out of %s stimulated neurons, %s (fraction) are bursting" % (
        stimulatedNeurons, burstingNeurons)
        )
    global cells
    choices = np.random.choice([0,1], stimulatedNeurons,
            p=[burstingNeurons,1.0-burstingNeurons]
            )
    spikeMode, burstMode = 0, 0
    for c in choices:
        cell = random.choice(cells.keys())
        soma = getSoma(cell)
        if c == 0:
            addPulseGen(soma, bursting=True)
            burstMode += 1
        else:
            addPulseGen(soma, bursting=False)
            spikeMode += 1
    mu.info("Total (spiking:%s, burting:%s) pulse-gen added" % (spikeMode, burstMode))

def simulate(simulationTime, solver='hsolve'):
    global args
    if solver == 'hsolve':
        solver = moose.HSolve('/hsolve')
        solver.dt = 0.5e-6
        solver.target = '/network'
    moose.reinit()
    moose.start(simulationTime)
    
def plotTables(total):
    global outputTables
    global tables

    #mu.saveRecords(inputTables, outfile = 'data.moose')
    #mu.saveRecords(outputTables, outfile = 'soma_axon_vm.moose')

    mu.plotRecords(inputTables, outfile = 'input.png', subplot=False)

    mu.info("Selecting %s tables randomly to plot" % total)
    keys = random.sample(outputTables.keys(), total)
    tabToPlot = {}
    for k in keys:
        tabToPlot[k] = outputTables[k]

    mu.plotRecords(tabToPlot, subplot=True
            , title = "Output tables"
            , legend=True, outfile = 'comp_vm.png')

    #mu.plotRecords(synTables, subplot=True, legend=True
    #        , title = "Synaptic tables"
    #        , outfile = 'synchan.png')

    plotAverage(outputTables, outfile="avg_soma.png")

def plotAverage(tables, outfile = None):
    global timeVec
    avgs = []
    for k in tables:
        vec = tables[k].vector
        if vec.max() > 0.7:
            mu.warn("Ignoring this table: Vm is too positive")
        if vec.min() < -0.1:
            mu.warn("Ignoring this table: Vm is too negative")
        else:
            avgs.append(tables[k].vector)

    clock = moose.Clock('/clock')
    yvec = np.average(avgs, axis=0)

    pylab.figure()
    timeVec = np.linspace(0, clock.currentTime, len(yvec))
    pylab.plot(timeVec, yvec)
    pylab.title("Average Vm (axons)")
    pylab.xlabel("Time (sec)")
    pylab.ylabel("Volts")
    if outfile:
        mu.info("Wrinting graph to %s" % outfile)
        pylab.savefig(outfile)
    else:
        pylab.show()

def plotSpikeRaster(spikeTables):
    pylab.figure()
    clock = moose.Clock('/clock')
    for i, tname in enumerate(spikeTables):
        yvec = spikeTables[tname]
        pylab.vlines(yvec, i, i+1, color='blue')
    pylab.title("Spike raster plot")
    pylab.ylabel("Index of axon")
    pylab.xlabel("Time (sec)")
    rasterFilename = 'spike_raster.png'
    mu.info("Saving raster plot to %s" % rasterFilename)
    pylab.savefig(rasterFilename)

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

    assert args.stimulated_neurons <= 1.0, "Fraction can't be larger than 1.0"
    stimulatedNeurons = int(args.num_cells * args.stimulated_neurons)
    setupStimulus(stimulatedNeurons, args.burst_mode)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')

    filters = args.total_plots[0:-1]
    total = args.total_plots[-1]

    setRecorder(comps, filters)

    mu.info("Simulating for %s seconds" % simulationTime)
    moose.setClock(1, 10e-6)
    moose.useClock(1, '/network/##', 'process')
    deactivateSomas(comps)
    moose.reinit()

    mu.verify()
    simulate(simulationTime)
    plotTables(int(total))

    totalSpikes = count_spikes(outputTables, args.spike_count_threshold)
    plotSpikeRaster(spikeTables)
    print("[RESULT] Total spikes in axons: %s" % totalSpikes)

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

    parser.add_argument('--spike_count_threshold', '-sct'
            , default = -10e-3
            , type = float
            , help = "When counting spikes, this value is taken as threshold"
            )

    parser.add_argument('--synaptic_weights', '-sw'
        , nargs = 2
        , default = [5e-3, -20e-3]
        , required = True
        , help = 'Synaptic weights [Excitatory, inhibitory]'
        )

    parser.add_argument('--input', '-in'
        , nargs = 3
        , required = True
        , help = 'Input pulset to neurons [frequency, width (sec), height (A)]'
        )

    parser.add_argument('--deactivated_somas', '-ds'
            , nargs = 2
            , type = float
            , default = [-0.070, 0.0]
            , help = "Fraction of somas to deactivate"
            )

    parser.add_argument('--total_plots', '-tp'
        , nargs = '+'
        , required = True
        , default = [ "axon", 10 ]
        , help = 'Total plots. Last entry is number of plots randomly selected'
            + '. Other entries are type of plots.'
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
