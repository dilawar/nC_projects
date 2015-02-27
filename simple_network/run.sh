#!/usr/bin/env bash

### NOTICE: Do not write negative numbers in sceintific notations.

## PARAMTERS
#nc: Number of cells
#ns: number of synapse
#es: Excitatory synapse (fraction of total)
#sn: Stimulated neurons (fraction of total)
#bm: Stimulated neurons firing in burst mode (fraction of sn)
#sw: synaptic weights [Excitatory, Inhib]
#st: synaptic threshold [Exc, Inhib]
#sct: spike detection threshold value
#in: input pulse, triplet [freq, width (S), height (A)]
#tp: types, num. plots of types (e.g. axon soma), num selected randomly e.g. 10
#rt: run time in seconds.
#kg: Potassium gbar (in pico-S).

#rm -rf *.png
set -x
python ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 100 -ns 500\
    -es 0.0 -sn 0.2 -bm 0.0 \
    -sw 0.001 -0.005 -st 0.1 0.1 \
    -tp soma 10 -kg 100\
    -in 40 0.005 0.000000001 -sct -0.010 -rt 0.3

