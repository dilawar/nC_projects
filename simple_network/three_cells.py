#!/usr/bin/env python
"""three_cells.py: 

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


import os, datetime
now = datetime.datetime.now()
datadir = "_data/%s" % (now.strftime('%Y%m%d-%H%M'))
if not os.path.isdir(datadir): os.makedirs(datadir)

def make_synapse(pre, post, excitatory = True):
    #: SpikeGen detects when presynaptic Vm crosses threshold and
    #: sends out a spike event

    mu.info("Synapse (Excitatory?=%s): %s --> %s" % (excitatory, pre.path,
        post.path))
    spikegen = moose.SpikeGen('%s/spikegen' % pre.path)
    spikegen.threshold = -55e-3 #float(args.synaptic_threshold[0])

    #: Create SynHandler to handle spike event input and set the
    #: activation input of synchan
    synhandler = moose.SimpleSynHandler('%s/synhandler' % post.path)
    synhandler.synapse.num = 1

    pre.connect('VmOut', spikegen, 'Vm')
    for i, syn in enumerate(synhandler.synapse):
        spikegen.connect('spikeOut', syn, 'addSpike')

    synchan = moose.SynChan('{}/synchan'.format(post.path))
    synchan.Gbar = 1e-8
    synchan.Ek = 0.0
    synchan.tau1, synchan.tau2 = 1e-3, 1e-3
    synchan.connect('channel', post, 'channel')

    for i in range(synhandler.synapse.num):
        synhandler.synapse[i].delay = 1e-3
        syn = synhandler.synapse[i]
        if excitatory:
            synhandler.synapse[i].weight = 10e-3 #float(args.synaptic_weights[0])
        else:
            synhandler.synapse[i].weight = -20e-3 # float(args.synaptic_weights[1])


    synhandler.connect('activationOut', synchan, 'activation')


def getCompType(cell, types=['axon'], which=0):
    comps = moose.wildcardFind('{}/##[TYPE=Compartment]'.format(cell))
    assert len(comps) > 0, "Cant find any compartment"
    tComps = []
    for c in comps:
        for t in types:
            if t in c.path.lower(): 
                tComps.append(c)

    assert len(tComps) > which, "Don't have enough compartment with type: %s" % types
    return tComps[which]


def makeTwoSynapses(cellDict):

    cells = cellDict.keys()
    if len(cells) < 2:
        print("Need at least two cells to make a synapse. Not making synapse")
        return 
    # select a compartment at random from each cell.
    pre = getCompType(cells[0], ["axon"], 0)
    post = getCompType(cells[1], ["dend"], 1)
    make_synapse(pre, post, True)

    pre = getCompType(cells[0], ["axon"], 0)
    post = getCompType(cells[2], ["dend"], 1)
    make_synapse(pre, post, True)
    
def loadCellModel(path, numCells):

    copyFrom = '/library/SampleCell'

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
    assert len(cells) > 1, "Check copyFrom variable %s" % copyFrom
    return cells 

def addPulseGen(c1, bursting, **kwargs):
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

def setRecorder(elems, field="getVm", outputDict = {}):
    assert len(elems) > 1, "No elements are given for setting records"
    [addTable(elem, field, outputDict)  for elem in elems]
    mu.info("Total %s recorders added" % len(outputDict))
    return outputDict

def addTable(elem, field='getVm', tabDict = {}):
    global outputTables, tables
    table = None
    table = moose.Table('{}/table'.format(elem.path))
    table.connect('requestOut', elem, field)
    tables[elem.path] = table
    tabDict[elem.path] = table
    return tabDict

def getSoma(cell):
    comp = moose.wildcardFind('{}/#[TYPE=Compartment]'.format(cell))
    for c in comp:
        if "soma" in c.path.lower():
            return c
    return None

def simulate(simulationTime, solver='hsolve'):

    if solver == 'hsolve':
        solver = moose.HSolve('/hsolve')
        solver.dt = 1e-6
        solver.target = '/network'
        moose.reinit()

    mu.info("Simulating for %s seconds" % simulationTime)
    moose.reinit()
    moose.start(simulationTime)
    mu.info("Total plots %s" % len(tables))

    mu.plotRecords(inputTables, outfile = 'input.png')
    mu.plotRecords(outputTables, subplot=True
            , title = "Output tables"
            , legend=True, outfile = 'comp_vm.png')

    mu.plotRecords(synTables, subplot=True, legend=True
            , title = "Gk (synchan) tables"
            , outfile = 'synchan.png')
    #pylab.show()

def main():
    moose.Neutral('/data')

    cellDict = loadCellModel('../simple_cell/generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1', 3)
    makeTwoSynapses(cellDict)

    cells = cellDict.keys()
    addPulseGen(getCompType(cells[0], ["soma"], 0), False)

    comps = moose.wildcardFind('/network/##[TYPE=Compartment]')
    setRecorder(comps, outputDict = outputTables )
    
    synchans = moose.wildcardFind('/network/##[TYPE=SynChan]')
    setRecorder(synchans, field = "getGk", outputDict = synTables)
    mu.verify()
    mu.writeGraphviz('network.dot')

    moose.setClock(0, 1e-5)
    moose.useClock(0, '/network/##', 'process')
    simulate(0.5)


if __name__ == '__main__':
    main()
