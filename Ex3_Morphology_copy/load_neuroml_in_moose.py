#!/usr/bin/env python

import sys
import moose
import moose.neuroml as nml
import moose.utils as mu

records_ = {}
somaPath_ = "Comp_1_0"
soma_ = None

def getSoma(compts):
    compName = somaPath_ #"Comp_1_0"
    for c in compts:
        c.Rm = 1e12
        if compName in c.path:
           soma_ = c
    return soma_

def setRecorder(soma):
    print("Setting records")
    table = moose.Table('/tableA')
    table.connect('requestOut', soma, 'getVm')
    records_[soma.path] = table

def verifyTables():
    print("Verifying result tables")
    for k in records_:
        print("%s: %s" % (k, mu.spike_train_simple_stat( records_[k].vector )))

def stimulus(compts):
    global soma_
    soma_ = getSoma(compts)
    assert soma_

    pulsegen = moose.PulseGen('/pulsegen')
    pulsegen.level[0] = 1e-9
    pulsegen.delay[0] = 20e-3
    pulsegen.width[0] = 60e-3
    pulsegen.delay[1] = 20

    pulsegenTable = moose.Table('/pulsegenTab')
    pulsegenTable.connect('requestOut', pulsegen, 'getOutputValue')

    pulsegen.connect('output', soma_, 'injectMsg')

    #records_['pulse_gen'] = pulsegenTable
    #soma_.inject = 1e-9
    moose.showfield(soma_)
    return soma_

def main():
    filename = sys.argv[1] #'./generatedNeuroML/Generated.net.xml'
    print("Loading into MOOSE: %s" % filename)

    nml.loadNeuroML_L123(filename)


    for p in moose.wildcardFind('/library/##'): p.tick = -1

    compts = moose.wildcardFind('/cells/##[TYPE=Compartment]')
    print("Total compartment in cell: %s" % len(compts))

    soma = stimulus(compts)
    setRecorder(soma)
    hsolve = moose.HSolve('/hsolve')
    #hsolve.dt = 50e-6
    hsolve.target = '/cells'
    moose.reinit()

    mu.summary()
    moose.start(0.1)
    print("Plotting")
    verifyTables()
    mu.plotRecords(records_, subplot = True) #, subplot=True, outfile='soma.svg')

if __name__ == '__main__':
    main()
