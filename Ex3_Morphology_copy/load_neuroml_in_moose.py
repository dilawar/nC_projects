#!/usr/bin/env python

import sys
import moose
import moose.neuroml as nml
import moose.utils as mu

def getSoma(compts):
    for c in compts:
        if "Comp_1_0" in c.path:
            return c

def setRecorder(soma):
    table = moose.Table('/table')
    table.connect('requestOut', soma, 'getVm')
    return table

def main():
    filename = './generatedNeuroML/L3Net_11-Jul-15_22-57-56.nml1'
    print("Loading into MOOSE: %s" % filename)
    nml.loadNeuroML_L123(filename)
    compts = moose.wildcardFind('/cells/##[TYPE=Compartment]')
    soma = getSoma(compts)
    table = setRecorder(soma)
    mu.verify()
    moose.reinit()
    moose.start(0.2)
    mu.plotRecords( { 'soma' : table }, outfile = 'soma.png')

if __name__ == '__main__':
    main()
