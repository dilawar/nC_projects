#!/usr/bin/env bash

### NOTE: Do not write negative numbers in sceintific notations.

## PARAMTERS
#nc: Number of cells
#ns: number of synapse
#es: Excitatory synapse (fraction of total)
#sn: Stimulated neurons (fraction of total)
#bm: Stimulated neurons firing in burst mode (fraction of sn)
#sw: synaptic weights [Excitatory, Inhib]
#st: synaptic threshold [Exc, Inhib]
#sct: spike detection threshold value (V)
#in: input pulse, triplet [freq, width (S), height (A)]
#tp: types, num. plots of types (e.g. axon soma), num selected       randomly e.g. 10
#ds: Deactivated somas [soma clamped at V, fraction of somas to deactivate]
#rt: simulation time in seconds.

#rm -rf *.png3
set -x
python  ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 100 \
    -ns 1000 \
    -es 0.7 \
    -sn 0.2 -bm 0.00005 \
    -sw 0.0025 -0.0025 \
    -st -0.055 -0.055 \
    -tp axon 5 \
    -in 40 0.005 0.000000001 \
    -ds -0.070 0.30 \
    -sct 0.015 \
    -rt 1

