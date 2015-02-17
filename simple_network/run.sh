#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f ../simple_cell/generatedNeuroML/L3Net_11-Feb-15_16-44-37.nml1 \
    -nc 10 -ns 20 -en 0.1 -sn 0.3 -bm 0.2 -st 1
if [ -f network.dot ]; then
    echo "Not dumping the topology"
    neato -Teps ./network.dot > ./network.eps
fi
