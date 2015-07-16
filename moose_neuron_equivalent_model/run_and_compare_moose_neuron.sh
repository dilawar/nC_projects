#!/bin/bash
set -e
rm -f ./soma.png
python ./load_neuroml_in_moose.py ./generatedNeuroML/L3Net_15-Jul-15_16-22-40.nml1
python compare.py ./moose_run_output.csv ./neuron_run_output.csv 
