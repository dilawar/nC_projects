#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f \
    ../simple_cell/generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 30 -ns 100 -en 0.3 -sn 0.3 -bm 0.3 -st 1
if [ -f network.dot ]; then
    echo "Not dumping the topology"
    neato -Teps ./network.dot > ./network.eps
fi
