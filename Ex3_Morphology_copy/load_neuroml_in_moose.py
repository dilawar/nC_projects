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
            return c

def setRecorder(soma):
    print("Setting records")
    table = moose.Table('/tableA')
    table.connect('requestOut', soma, 'getVm')
    records_[soma.path] = table

def stimulus(compts):
    global soma_
    soma_ = getSoma(compts)
    assert soma_
    #pulsegen = moose.PulseGen('/pulsegen')
    #pulsegen.level[0] = 1e-10
    #pulsegen.connect('output', soma_, 'injectMsg')
    soma_.inject = 1e-9
    return soma_

def main():
    filename = sys.argv[1] #'./generatedNeuroML/Generated.net.xml'
    print("Loading into MOOSE: %s" % filename)
    nml.loadNeuroML_L123(filename)
    moose.delete('/library')

    compts = moose.wildcardFind('/cells/##[TYPE=Compartment]')
    soma = stimulus(compts)
    setRecorder(soma)
    moose.reinit()
    moose.start(0.1)
    print("Plotting")
    mu.plotRecords(records_) # outfile='soma.png')

if __name__ == '__main__':
    main()
