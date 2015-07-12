#!/usr/bin/env python

import sys
import moose
import moose.neuroml as nml
import moose.utils as mu
import moose.backend as backend

records_ = {}
somaPath_ = "Comp_1_0"
soma_ = None

def getSoma(compts):
    compName = somaPath_ #"Comp_1_0"
    for c in compts:
        if compName in c.path:
            soma_ = c
            return c

def setRecorder():
    print("Setting records")
    table = moose.Table('/tableA')
    table.connect('requestOut', soma_, 'getVm')
    records_[soma_.path] = table

def stimulus(compts):
    global soma_
    soma_ = getSoma(compts)
    assert soma_
    soma_.inject = 1e-10

def main():
    filename = sys.argv[1] #'./generatedNeuroML/Generated.net.xml'
    print("Loading into MOOSE: %s" % filename)
    nml.loadNeuroML_L123(filename)
    for path in moose.wildcardFind('/library/##'):
        path.tick = -1
    compts = moose.wildcardFind('/##[TYPE=Compartment]')
    stimulus(compts)
    setRecorder()
    moose.start(0.1)
    print("Plotting")
    mu.plotRecords(records_, outfile='soma.png')

if __name__ == '__main__':
    main()
