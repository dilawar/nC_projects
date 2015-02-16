#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f ../simple_cell/generatedNeuroML/L3Net_11-Feb-15_16-44-37.nml1 \
    -n 100 -s 1000 -p 0.5 -sn 0.5 -bm 0 -st 1e-1
if [ -f network.dot ]; then
    echo "Not dumping the topology"
    neato -Teps ./network.dot > ./network.eps
fi
