#!/usr/bin/env bash
set -x
rm -f network.dot
python ./simple_network.py -f \
    ./ca1_network/CA1.morph.xml \
    -nc 30 -ns 100 -en 0.5 -sn 0.3 -bm 0.3 -st 0.1
if [ -f network.dot ]; then
    echo "Not dumping the topology"
    neato -Teps ./network.dot > ./network.eps
fi
