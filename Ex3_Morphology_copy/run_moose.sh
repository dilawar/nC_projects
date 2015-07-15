#!/bin/bash
set -e
rm -f ./soma.png
python ./load_neuroml_in_moose.py ./generatedNeuroML/L3Net_15-Jul-15_16-22-40.nml1
#if [ -f soma.svg ]; then
    #display ./soma.svg
#fi
