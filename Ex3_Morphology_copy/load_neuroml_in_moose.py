#!/usr/bin/env python

import sys
import moose
import moose.neuroml as nml
import moose.utils as mu
import moose.backend as backend

records_ = {}

def getSoma(compts):
    compName = "Comp_1_0"
    for c in compts:
        if compName in c.path:
            return compName, c

def setRecorder(compt):
    table = moose.Table('/table')
    table.connect('requestOut', compt, 'getVm')
    records_[compt.path] = table

def getStimulus():
    stims = moose.wildcardFind('/elec/##[TYPE=DiffAmp]')
    table1 = moose.Table('/table2')  
    print stims[-1].neighbors['output']
    table1.connect('requestOut', stims[-1], 'getOutputValue')
    records_[ stims[-1].path ] = table1

def simulate(time):
    compts = moose.wildcardFind('/cells/##[TYPE=Compartment]')
    compName, compt = getSoma(compts)
    setRecorder(compt)
    mu.summary()
    moose.reinit()
    moose.start(time)
    #mu.plotRecords( { compName : table }, outfile = 'soma.png')
    mu.plotRecords(records_, subplot=True) #, outfile = 'soma.png')
    #print("Min, Max, Avg: %s, %s, %s" % (table.vector.min(), table.vector.max()
    #    , table.vector.mean()))


def main():
    filename = sys.argv[1] #'./generatedNeuroML/Generated.net.xml'
    print("Loading into MOOSE: %s" % filename)
    nml.loadNeuroML_L123(filename)
    for path in moose.wildcardFind('/library/##'):
        path.tick = -1
    getStimulus()
    simulate(0.1)

if __name__ == '__main__':
    main()
