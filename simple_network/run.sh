#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f \
    ../simple_cell/generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 1 -ns 0 -en 1 -sn 1.0 -bm 0 -st 1
if [ -f network.dot ]; then
    echo "Not dumping the topology"
    neato -Teps ./network.dot > ./network.eps
fi
