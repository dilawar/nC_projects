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
#rt: run time in seconds.

#rm -rf *.png
set -x
python ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 100 -ns 500\
    -es 1.0 -sn 0.1 -bm 0.2 \
    -sw 0.1 -0.0050 -st -0.055 -0.055 \
    -in 4.0 0.005 0.000000001 -sct -0.00 -rt 0.5

