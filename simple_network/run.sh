#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f ../simple_cell/generatedNeuroML/L3Net_11-Feb-15_16-44-37.nml1 \
    -n 4 -s 100 -p 0.5
if [ -f network.dot ]; then
neato -Teps ./network.dot > ./network.eps
fi
