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
        if compName in c.path:
            return c

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
    pulsegen.width[0] = 40e-3

    pulsegenTable = moose.Table('/pulsegenTab')
    pulsegenTable.connect('requestOut', pulsegen, 'getOutputValue')

    pulsegen.connect('output', soma_, 'injectMsg')

    records_['pulse_gen'] = pulsegenTable
    #soma_.inject = 1e-9
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
    mu.summary()
    moose.start(0.1)
    print("Plotting")
    mu.plotRecords(records_, subplot=True)
    verifyTables()

if __name__ == '__main__':
    main()
