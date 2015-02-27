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
#cn: Clamped neurons (fraction of total neurons).

#rm -rf *.png
set -x
python ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 100 -ns 1000\
    -es 0.8 -sn 0.2 -bm 0.0001 \
    -sw 0.1 -0.0050 -st -0.055 -0.055 \
    -tp soma 20 -cn 0.1 \
    -in 40 0.005 0.000000001 -sct 0.00 -rt 0.1
